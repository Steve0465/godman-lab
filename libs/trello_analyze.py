from __future__ import annotations

import json
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ListInfo:
    id: str
    name: str
    closed: bool = False


@dataclass
class Card:
    id: str
    name: str
    idList: str
    closed: bool
    dateLastActivity: Optional[str] = None
    due: Optional[str] = None
    start: Optional[str] = None
    labels: Optional[List[Dict[str, Any]]] = None
    idMembers: Optional[List[str]] = None


@dataclass
class ActionMove:
    card_id: str
    from_list_id: str
    to_list_id: str
    timestamp: datetime


def _parse_dt(dt: Optional[str]) -> Optional[datetime]:
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def infer_list_roles(list_names: List[str], mapping_path: Optional[str] = None) -> Dict[str, str]:
    """Infer list roles mapping list name -> role.

    If mapping_path is provided:
      - If endswith .json, parse JSON
      - If endswith .yml/.yaml, try PyYAML; if unavailable, raise a clear error
    Otherwise, infer heuristically using keywords.
    Roles: backlog, todo, in_progress, review, done
    """
    explicit_map: Dict[str, str] = {}

    if mapping_path:
        p = Path(mapping_path)
        data: Dict[str, List[str]]
        if p.suffix.lower() == ".json":
            data = json.loads(p.read_text())
        else:
            try:
                import yaml  # type: ignore

                data = yaml.safe_load(p.read_text()) or {}
            except Exception as e:
                raise RuntimeError(
                    "Mapping file appears to be YAML; install PyYAML or provide JSON mapping."
                ) from e
        # reverse mapping to list->role
        for role, names in data.items():
            for n in names or []:
                explicit_map[n.strip().lower()] = role

    # Heuristic mapping
    def classify(name: str) -> str:
        lname = name.strip().lower()
        if lname in explicit_map:
            return explicit_map[lname]
        if any(k in lname for k in ["backlog", "inbox", "icebox", "ideas"]):
            return "backlog"
        if any(k in lname for k in ["todo", "to do", "ready", "next"]):
            return "todo"
        if any(k in lname for k in ["doing", "in progress", "wip", "progress", "dev", "build"]):
            return "in_progress"
        if any(k in lname for k in ["review", "qa", "verify", "test"]):
            return "review"
        if any(k in lname for k in ["done", "complete", "finished", "archive", "shipped"]):
            return "done"
        # default bucket
        return "other"

    return {name: classify(name) for name in list_names}


def parse_list_transitions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract normalized list movement events from actions.

    Input actions are Trello action dicts. We capture updateCard with data.listBefore/listAfter.
    Output: dicts with keys card_id, from_list_id, to_list_id, timestamp (ISO).
    """
    events: List[Dict[str, Any]] = []
    for a in actions:
        if a.get("type") != "updateCard":
            continue
        data = a.get("data", {})
        if not data:
            continue
        if "listBefore" in data and "listAfter" in data:
            card = data.get("card", {})
            ts = a.get("date")
            events.append(
                {
                    "card_id": card.get("id"),
                    "from_list_id": data["listBefore"].get("id"),
                    "to_list_id": data["listAfter"].get("id"),
                    "timestamp": ts,
                }
            )
    # Sort chronologically
    events.sort(key=lambda e: e.get("timestamp") or "")
    return events


def _list_id_name_map(snapshot: Dict[str, Any]) -> Dict[str, str]:
    return {l.get("id"): l.get("name") for l in snapshot.get("lists", [])}


def compute_metrics(snapshot: Dict[str, Any], actions: List[Dict[str, Any]], list_role_map: Dict[str, str]) -> Dict[str, Any]:
    """Compute inventory, hygiene, label/member usage, and flow metrics.

    Returns a dictionary suitable for markdown report generation.
    """
    lists = snapshot.get("lists", [])
    cards = snapshot.get("cards", [])
    members = snapshot.get("members", [])

    list_id_to_name = _list_id_name_map(snapshot)
    list_name_to_role = list_role_map
    list_id_to_role = {lid: list_name_to_role.get(list_id_to_name.get(lid, ""), "other") for lid in list_id_to_name}

    # Inventory counts
    cards_per_list = Counter(c.get("idList") for c in cards)
    open_cards = [c for c in cards if not c.get("closed")]
    closed_cards = [c for c in cards if c.get("closed")]
    unassigned_count = sum(1 for c in open_cards if not c.get("idMembers"))

    # Stale cards (> N days since last activity)
    N = 14
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=N)
    def is_stale(c: Dict[str, Any]) -> bool:
        last = _parse_dt(c.get("dateLastActivity"))
        return bool(last and last < stale_cutoff and not c.get("closed"))
    stale_cards = [c for c in cards if is_stale(c)]

    # Due date hygiene
    with_due = [c for c in cards if c.get("due")]
    without_due = [c for c in cards if not c.get("due")]
    overdue = []
    completed_after_due = 0
    now = datetime.now(timezone.utc)
    for c in cards:
        due = _parse_dt(c.get("due"))
        if not due:
            continue
        if due < now and not c.get("closed"):
            overdue.append(c)
        # Naive heuristic: if closed and due exists and lastActivity>due
        if c.get("closed"):
            last = _parse_dt(c.get("dateLastActivity"))
            if last and due and last > due:
                completed_after_due += 1

    # Label usage
    label_counter: Counter[str] = Counter()
    labeled_cards = 0
    for c in cards:
        labels = c.get("labels", []) or []
        if labels:
            labeled_cards += 1
        for lab in labels:
            name = lab.get("name") or lab.get("color") or "(unnamed)"
            label_counter[name] += 1
    unlabeled_pct = 0.0 if not cards else (1 - labeled_cards / len(cards)) * 100.0
    # Shannon entropy of label distribution
    total_labels = sum(label_counter.values())
    entropy = 0.0
    if total_labels > 0:
        for count in label_counter.values():
            p = count / total_labels
            entropy -= p * math.log(p, 2)

    # Member load
    member_card_count: Counter[str] = Counter()
    for c in open_cards:
        for m in c.get("idMembers", []) or []:
            member_card_count[m] += 1

    # Flow metrics from transitions
    transitions = parse_list_transitions(actions)
    # Time in list estimates per card using transition sequence
    card_events: Dict[str, List[Tuple[datetime, str]]] = defaultdict(list)
    for ev in transitions:
        ts = _parse_dt(ev.get("timestamp"))
        if ts and ev.get("to_list_id"):
            card_events[ev["card_id"]].append((ts, ev["to_list_id"]))
    for evs in card_events.values():
        evs.sort(key=lambda t: t[0])

    # Compute time in list by card by diffing consecutive events
    list_durations: Dict[str, List[float]] = defaultdict(list)  # list_id -> hours
    for cid, evs in card_events.items():
        for i in range(1, len(evs)):
            prev_ts, prev_list = evs[i - 1]
            ts, _ = evs[i]
            hrs = (ts - prev_ts).total_seconds() / 3600.0
            list_durations[prev_list].append(hrs)

    def _agg_hours(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"avg_h": 0.0, "median_h": 0.0}
        vals = sorted(values)
        n = len(vals)
        median = vals[n // 2] if n % 2 == 1 else (vals[n // 2 - 1] + vals[n // 2]) / 2
        return {"avg_h": sum(vals) / n, "median_h": median}

    time_in_list = {list_id_to_name.get(lid, lid): _agg_hours(durs) for lid, durs in list_durations.items()}

    # Cycle time: first in_progress to first done per card
    role_by_list = list_id_to_role
    cycle_times_h: List[float] = []
    done_transitions_per_week: Counter[str] = Counter()
    for cid, evs in card_events.items():
        first_ip: Optional[datetime] = None
        first_done: Optional[datetime] = None
        for ts, lid in evs:
            role = role_by_list.get(lid, "other")
            if not first_ip and role in {"in_progress", "review"}:
                first_ip = ts
            if role == "done":
                first_done = ts
                break
        if first_ip and first_done and first_done > first_ip:
            cycle_times_h.append((first_done - first_ip).total_seconds() / 3600.0)
            week_key = first_done.strftime("%Y-%W")
            done_transitions_per_week[week_key] += 1

    throughput_per_week = dict(done_transitions_per_week)

    # Bottleneck identification: high WIP + high time-in-list
    wip_counts_by_list: Dict[str, int] = defaultdict(int)
    for c in open_cards:
        wip_counts_by_list[c.get("idList")] += 1
    bottlenecks: List[str] = []
    for lid, wip in wip_counts_by_list.items():
        role = role_by_list.get(lid, "other")
        if role in {"in_progress", "review"}:
            stats = _agg_hours(list_durations.get(lid, []))
            if wip >= max(5, int(len(open_cards) * 0.2)) and stats["avg_h"] > 24:
                bottlenecks.append(f"{list_id_to_name.get(lid, lid)} (WIP={wip}, avg~{int(stats['avg_h'])}h)")

    # Board smells / weaknesses
    smells: List[str] = []
    # Too many WIP cards in progress
    total_wip_ip = sum(wip_counts_by_list[lid] for lid, r in role_by_list.items() if r == "in_progress")
    if total_wip_ip > max(5, int(len(open_cards) * 0.33)):
        smells.append("High WIP in progress lists; consider WIP limits")
    # Backlog too large and untouched
    backlog_ids = [lid for lid, r in role_by_list.items() if r == "backlog"]
    backlog_size = sum(cards_per_list.get(lid, 0) for lid in backlog_ids)
    if backlog_size > max(50, int(len(cards) * 0.5)):
        smells.append("Very large backlog; consider pruning/triage cadence")
    # High variance cycle time
    if len(cycle_times_h) >= 5:
        mean = sum(cycle_times_h) / len(cycle_times_h)
        variance = sum((x - mean) ** 2 for x in cycle_times_h) / len(cycle_times_h)
        std = math.sqrt(variance)
        if std > mean:
            smells.append("High cycle time variability; stabilize workflow")
    # Unclear done definition
    done_list_count = sum(1 for lid, r in role_by_list.items() if r == "done")
    if done_list_count > 1:
        smells.append("Multiple 'Done' lists; clarify single definition of done or final sink")
    # Many cards missing due dates or owners
    if len(without_due) > len(cards) * 0.6:
        smells.append("Most cards missing due dates; define/encourage due-date hygiene")
    if unassigned_count > len(open_cards) * 0.5:
        smells.append("Many cards lack owners; enforce assignment policy")

    metrics: Dict[str, Any] = {
        "inventory": {
            "cards_per_list": {list_id_to_name.get(k, k): v for k, v in cards_per_list.items()},
            "open": len(open_cards),
            "closed": len(closed_cards),
            "unassigned": unassigned_count,
        },
        "stale": {
            "threshold_days": 14,
            "count": len(stale_cards),
            "examples": [c.get("name") for c in stale_cards[:10]],
        },
        "due_hygiene": {
            "missing_due_pct": (len(without_due) / len(cards) * 100.0) if cards else 0.0,
            "overdue_pct": (len(overdue) / len(cards) * 100.0) if cards else 0.0,
            "completed_after_due": completed_after_due,
        },
        "labels": {
            "top": label_counter.most_common(10),
            "unlabeled_pct": unlabeled_pct,
            "entropy": entropy,
        },
        "members": {
            "load_open_cards": dict(member_card_count),
            "total_members": len(members),
        },
        "flow": {
            "time_in_list": time_in_list,
            "cycle_time_h": {
                "count": len(cycle_times_h),
                "avg": (sum(cycle_times_h) / len(cycle_times_h)) if cycle_times_h else 0.0,
                "median": (sorted(cycle_times_h)[len(cycle_times_h)//2] if cycle_times_h else 0.0),
            },
            "throughput_per_week": throughput_per_week,
            "bottlenecks": bottlenecks,
        },
        "smells": smells,
        "snapshot_meta": {
            "list_roles": {list_id_to_name.get(lid, lid): role_by_list.get(lid, "other") for lid in list_id_to_name},
        },
    }

    return metrics


def generate_audit_report(metrics: Dict[str, Any], snapshot_meta: Dict[str, Any], out_path: str) -> None:
    """Write a markdown audit report summarizing findings and recommendations."""
    lists = snapshot_meta.get("lists", [])
    labels = snapshot_meta.get("labels", []) if snapshot_meta else []
    members = snapshot_meta.get("members", []) if snapshot_meta else []

    lines: List[str] = []
    lines.append(f"# Trello Board Audit Report\n")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")

    # Setup section
    lines.append("## Setup Snapshot")
    lines.append("### Lists")
    for l in lists:
        name = l.get("name")
        lines.append(f"- {name}")
    lines.append("\n### Labels")
    for lab in labels[:20]:
        nm = lab.get("name") or lab.get("color")
        lines.append(f"- {nm}")
    lines.append("\n### Members")
    for m in members:
        lines.append(f"- {m.get('fullName')} (@{m.get('username')})")

    # Inventory / cadence
    inv = metrics.get("inventory", {})
    lines.append("\n## Inventory & Cadence")
    lines.append(f"- Open cards: {inv.get('open', 0)} (closed: {inv.get('closed', 0)})")
    lines.append("- Cards per list:")
    for lst, cnt in sorted(inv.get("cards_per_list", {}).items(), key=lambda x: -x[1]):
        lines.append(f"  - {lst}: {cnt}")

    # Strengths
    strengths: List[str] = []
    if metrics["labels"]["entropy"] > 1.0:
        strengths.append("Labels used with reasonable diversity")
    if metrics["flow"]["cycle_time_h"]["count"] >= 10:
        strengths.append("Sufficient done transitions to estimate cycle time")
    if inv.get("unassigned", 0) <= max(3, int(inv.get("open", 0) * 0.1)):
        strengths.append("Most cards have owners assigned")

    # Weaknesses from smells
    weaknesses: List[str] = metrics.get("smells", [])

    lines.append("\n## Strengths")
    if strengths:
        for s in strengths:
            lines.append(f"- {s}")
    else:
        lines.append("- No strong positives identified yet; continue collecting data")

    lines.append("\n## Weaknesses / Risks")
    if weaknesses:
        for w in weaknesses:
            lines.append(f"- {w}")
    else:
        lines.append("- No critical risks detected")

    # Pattern analysis
    flow = metrics.get("flow", {})
    lines.append("\n## Flow & Pattern Analysis")
    ct = flow.get("cycle_time_h", {})
    lines.append(f"- Cycle time (avg): {ct.get('avg', 0):.1f}h, median: {ct.get('median', 0):.1f}h, n={ct.get('count', 0)}")
    lines.append("- Time in list (median hours):")
    for lst, stats in flow.get("time_in_list", {}).items():
        lines.append(f"  - {lst}: {stats.get('median_h', 0):.1f}h (avg {stats.get('avg_h', 0):.1f}h)")
    lines.append("- Throughput per week (cards entering Done):")
    for wk, cnt in sorted(flow.get("throughput_per_week", {}).items()):
        lines.append(f"  - {wk}: {cnt}")
    if flow.get("bottlenecks"):
        lines.append("- Potential bottlenecks:")
        for b in flow["bottlenecks"]:
            lines.append(f"  - {b}")

    # Recommendations
    lines.append("\n## Recommendations - Next 5 Improvements")
    recs: List[str] = []
    if inv.get("unassigned", 0) > max(3, int(inv.get("open", 0) * 0.25)):
        recs.append("Enforce owner assignment before moving to In Progress")
    if metrics["due_hygiene"]["missing_due_pct"] > 50:
        recs.append("Set due dates on all in-progress work and critical backlog items")
    if metrics["due_hygiene"]["overdue_pct"] > 10:
        recs.append("Triage overdue items weekly; renegotiate or close stale work")
    if flow.get("bottlenecks"):
        recs.append("Add WIP limits to bottleneck lists and implement pull policies")
    if ct.get("avg", 0) > 72:
        recs.append("Break down large work items; target 1-2 day cycle times")
    if not recs:
        recs = [
            "Establish weekly backlog grooming cadence",
            "Define clear entry/exit criteria for each list",
            "Introduce explicit 'Review' stage if missing",
            "Automate stale card reminders (>14d no activity)",
            "Create a 'Done (This Week)' list to visualize throughput",
        ]
    for r in recs[:5]:
        lines.append(f"- [ ] {r}")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines))
    logger.info("Wrote audit report to %s", out_path)
