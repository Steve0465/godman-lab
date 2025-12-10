#!/usr/bin/env python3
"""
Audit Snapshot Generator - Stdlib-only tool for capturing repository state.

Generates comprehensive snapshot files for repository auditing and analysis.
Outputs both human-readable text and structured JSON formats.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class AuditSnapshot:
    """Generate comprehensive repository audit snapshots."""
    
    def __init__(self, repo_root: Path, max_lines_per_section: int = 200):
        self.repo_root = repo_root
        self.max_lines = max_lines_per_section
        self.snapshot_data: Dict[str, Any] = {}
    
    def run_git_command(self, args: List[str]) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except Exception as e:
            return f"[Error: {e}]"
    
    def collect_git_info(self) -> Dict[str, str]:
        """Collect git repository information."""
        return {
            "branch": self.run_git_command(["rev-parse", "--abbrev-ref", "HEAD"]),
            "status": self.run_git_command(["status", "-sb"]),
            "last_commit": self.run_git_command(["log", "-1", "--oneline"]),
        }
    
    def collect_directory_structure(self) -> Dict[str, Any]:
        """Collect directory structure and file counts."""
        structure = {
            "top_level": [],
            "python_counts": {}
        }
        
        # Get top-level directories (maxdepth 2)
        try:
            result = subprocess.run(
                ["find", ".", "-maxdepth", "2", "-type", "d"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            dirs = [d for d in result.stdout.split("\n") 
                   if d and not any(x in d for x in [".venv", "__pycache__", ".git", "egg-info"])]
            structure["top_level"] = sorted(dirs)[:50]
        except Exception as e:
            structure["top_level"] = [f"[Error: {e}]"]
        
        # Count Python files in major folders
        major_folders = ["cli", "godman_ai", "libs", "workflows", "ocr"]
        for folder in major_folders:
            folder_path = self.repo_root / folder
            if folder_path.exists():
                try:
                    result = subprocess.run(
                        ["find", str(folder_path), "-name", "*.py", "-type", "f"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    count = len([l for l in result.stdout.split("\n") if l.strip()])
                    structure["python_counts"][folder] = count
                except Exception:
                    structure["python_counts"][folder] = 0
        
        return structure
    
    def read_file_content(self, file_path: Path, max_lines: int = 40) -> Tuple[int, str]:
        """Read file and return line count + first N lines."""
        if not file_path.exists():
            return 0, "[File not found]"
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                total_lines = len(lines)
                preview = "".join(lines[:max_lines])
                if total_lines > max_lines:
                    preview += f"\n... [{total_lines - max_lines} more lines]\n"
                return total_lines, preview
        except Exception as e:
            return 0, f"[Error reading file: {e}]"
    
    def collect_key_files(self) -> Dict[str, Dict[str, Any]]:
        """Collect information about key files."""
        key_files = {
            "cli/codex_runner.py": {},
            ".codex/AGENTS.md": {},
            ".codex/tools.json": {},
            "libs/tool_runner.py": {},
        }
        
        # Add orchestrator files
        orchestrator_dir = self.repo_root / "godman_ai" / "orchestrator"
        if orchestrator_dir.exists():
            for f in orchestrator_dir.glob("*.py"):
                key_files[str(f.relative_to(self.repo_root))] = {}
        
        # Add agent files
        agents_dir = self.repo_root / "godman_ai" / "agents"
        if agents_dir.exists():
            for f in agents_dir.glob("*.py"):
                key_files[str(f.relative_to(self.repo_root))] = {}
        
        # Add LLM files
        llm_dir = self.repo_root / "godman_ai" / "llm"
        if llm_dir.exists():
            for f in llm_dir.glob("*.py"):
                key_files[str(f.relative_to(self.repo_root))] = {}
        
        # Add tools files
        tools_dir = self.repo_root / "godman_ai" / "tools"
        if tools_dir.exists():
            for f in tools_dir.glob("*.py"):
                key_files[str(f.relative_to(self.repo_root))] = {}
        
        # Add workflow files
        workflows_dir = self.repo_root / "workflows"
        if workflows_dir.exists():
            for f in workflows_dir.glob("*.py"):
                key_files[str(f.relative_to(self.repo_root))] = {}
        
        # Add OCR files
        ocr_dir = self.repo_root / "ocr"
        if ocr_dir.exists():
            for f in ocr_dir.glob("*.py"):
                key_files[str(f.relative_to(self.repo_root))] = {}
        
        # Read each file
        for file_path_str in sorted(key_files.keys()):
            file_path = self.repo_root / file_path_str
            line_count, content = self.read_file_content(file_path, max_lines=40)
            key_files[file_path_str] = {
                "path": file_path_str,
                "line_count": line_count,
                "preview": content
            }
        
        return key_files
    
    def run_ripgrep_search(self, pattern: str) -> List[str]:
        """Run ripgrep search and return results."""
        try:
            result = subprocess.run(
                ["rg", "-n", pattern, "--type", "py"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            lines = result.stdout.split("\n")
            # Limit to max_lines
            if len(lines) > self.max_lines:
                lines = lines[:self.max_lines] + [f"... [{len(lines) - self.max_lines} more results]"]
            return [l for l in lines if l.strip()]
        except FileNotFoundError:
            return ["[ripgrep not available]"]
        except Exception as e:
            return [f"[Error: {e}]"]
    
    def collect_search_patterns(self) -> Dict[str, List[str]]:
        """Collect ripgrep search results for key patterns."""
        patterns = {
            "class_agents": r"class .*Agent",
            "tool_runner": "ToolRunner",
            "tool_decorator": "@tool",
            "tool_registry": "TOOL_REGISTRY",
            "register_tool": "register_tool",
            "router_v2": "router_v2",
            "tool_router": "tool_router",
            "ollama": "ollama",
            "openai": "OPENAI",
            "model_registry": "MODEL_REGISTRY",
            "responses_api": "Responses",
            "codex": "CODEX_",
        }
        
        results = {}
        for name, pattern in patterns.items():
            results[name] = self.run_ripgrep_search(pattern)
        
        return results
    
    def generate_snapshot(self) -> Dict[str, Any]:
        """Generate complete snapshot data."""
        print("Collecting git information...", file=sys.stderr)
        git_info = self.collect_git_info()
        
        print("Analyzing directory structure...", file=sys.stderr)
        structure = self.collect_directory_structure()
        
        print("Reading key files...", file=sys.stderr)
        key_files = self.collect_key_files()
        
        print("Running pattern searches...", file=sys.stderr)
        searches = self.collect_search_patterns()
        
        snapshot = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "repo_root": str(self.repo_root),
            },
            "git": git_info,
            "structure": structure,
            "key_files": key_files,
            "searches": searches,
        }
        
        self.snapshot_data = snapshot
        return snapshot
    
    def write_text_output(self, output_path: Path) -> None:
        """Write human-readable text snapshot."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GODMAN-LAB AUDIT SNAPSHOT\n")
            f.write("=" * 80 + "\n\n")
            
            # Metadata
            f.write("Generated: {}\n".format(self.snapshot_data["metadata"]["generated_at"]))
            f.write("Repo Root: {}\n\n".format(self.snapshot_data["metadata"]["repo_root"]))
            
            # Git Info
            f.write("-" * 80 + "\n")
            f.write("GIT INFORMATION\n")
            f.write("-" * 80 + "\n")
            f.write("Branch: {}\n".format(self.snapshot_data["git"]["branch"]))
            f.write("Last Commit: {}\n\n".format(self.snapshot_data["git"]["last_commit"]))
            f.write("Status:\n{}\n\n".format(self.snapshot_data["git"]["status"]))
            
            # Directory Structure
            f.write("-" * 80 + "\n")
            f.write("DIRECTORY STRUCTURE\n")
            f.write("-" * 80 + "\n")
            f.write("Top-level directories:\n")
            for d in self.snapshot_data["structure"]["top_level"]:
                f.write(f"  {d}\n")
            f.write("\nPython file counts:\n")
            for folder, count in self.snapshot_data["structure"]["python_counts"].items():
                f.write(f"  {folder}: {count} files\n")
            f.write("\n")
            
            # Key Files
            f.write("-" * 80 + "\n")
            f.write("KEY FILES\n")
            f.write("-" * 80 + "\n")
            for file_path, info in self.snapshot_data["key_files"].items():
                f.write(f"\n### {file_path} ({info['line_count']} lines) ###\n\n")
                f.write(info["preview"])
                f.write("\n")
            
            # Pattern Searches
            f.write("-" * 80 + "\n")
            f.write("PATTERN SEARCHES\n")
            f.write("-" * 80 + "\n")
            for pattern_name, results in self.snapshot_data["searches"].items():
                f.write(f"\n### {pattern_name.upper()} ###\n")
                for line in results:
                    f.write(f"{line}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF SNAPSHOT\n")
            f.write("=" * 80 + "\n")
    
    def write_json_output(self, output_path: Path) -> None:
        """Write structured JSON snapshot."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.snapshot_data, f, indent=2)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive audit snapshot of godman-lab repository"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="docs/audit",
        help="Output directory for snapshot files (default: docs/audit)"
    )
    parser.add_argument(
        "--max-lines-per-section",
        type=int,
        default=200,
        help="Maximum lines per search section (default: 200)"
    )
    
    args = parser.parse_args()
    
    # Determine repo root (assume script is in scripts/ directory)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    
    # Create output directory
    out_dir = repo_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating audit snapshot for: {repo_root}", file=sys.stderr)
    print(f"Output directory: {out_dir}", file=sys.stderr)
    
    # Generate snapshot
    auditor = AuditSnapshot(repo_root, max_lines_per_section=args.max_lines_per_section)
    snapshot = auditor.generate_snapshot()
    
    # Write outputs
    text_path = out_dir / "snapshot.txt"
    json_path = out_dir / "snapshot.json"
    
    print(f"Writing text snapshot to: {text_path}", file=sys.stderr)
    auditor.write_text_output(text_path)
    
    print(f"Writing JSON snapshot to: {json_path}", file=sys.stderr)
    auditor.write_json_output(json_path)
    
    print("\n✓ Snapshot generation complete!", file=sys.stderr)
    print(f"  Text: {text_path}", file=sys.stderr)
    print(f"  JSON: {json_path}", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
