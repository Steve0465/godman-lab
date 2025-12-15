import json
from pathlib import Path

# Add libs path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'libs'))

from trello_analyze import parse_list_transitions, compute_metrics, infer_list_roles


def test_parse_list_transitions_basic():
    actions = [
        {
            "type": "updateCard",
            "date": "2024-11-01T10:00:00Z",
            "data": {
                "card": {"id": "c1"},
                "listBefore": {"id": "L1", "name": "To Do"},
                "listAfter": {"id": "L2", "name": "Doing"},
            },
        },
        {
            "type": "updateCard",
            "date": "2024-11-02T12:00:00Z",
            "data": {
                "card": {"id": "c1"},
                "listBefore": {"id": "L2", "name": "Doing"},
                "listAfter": {"id": "L3", "name": "Done"},
            },
        },
    ]

    events = parse_list_transitions(actions)
    assert len(events) == 2
    assert events[0]["from_list_id"] == "L1"
    assert events[1]["to_list_id"] == "L3"


def test_compute_cycle_time_simple():
    snapshot = {
        "lists": [
            {"id": "L1", "name": "To Do"},
            {"id": "L2", "name": "Doing"},
            {"id": "L3", "name": "Done"},
        ],
        "cards": [
            {
                "id": "c1",
                "name": "Task 1",
                "idList": "L3",
                "closed": False,
                "dateLastActivity": "2024-11-02T12:00:00Z",
            }
        ],
        "members": [],
    }

    actions = [
        {
            "type": "updateCard",
            "date": "2024-11-01T10:00:00Z",
            "data": {
                "card": {"id": "c1"},
                "listBefore": {"id": "L1", "name": "To Do"},
                "listAfter": {"id": "L2", "name": "Doing"},
            },
        },
        {
            "type": "updateCard",
            "date": "2024-11-02T10:00:00Z",
            "data": {
                "card": {"id": "c1"},
                "listBefore": {"id": "L2", "name": "Doing"},
                "listAfter": {"id": "L3", "name": "Done"},
            },
        },
    ]

    list_names = [l["name"] for l in snapshot["lists"]]
    roles = infer_list_roles(list_names)
    metrics = compute_metrics(snapshot, actions, roles)

    ct = metrics["flow"]["cycle_time_h"]
    assert ct["count"] == 1
    # 24 hours from 2024-11-01T10 to 2024-11-02T10
    assert abs(ct["avg"] - 24.0) < 0.01
