import argparse
import json
import os
import sys
from typing import Dict, Tuple

import yaml

from codex_client import CodexClient
from env_crypto import encrypt_env
from file_manager import FileManager
from meta_core import TASKS_DIR, run_task
from project_scanner import ProjectScanner
from prompt_builder import PromptBuilder
from supervisor_runner import run_supervisor_cycle
from task_archiver import (
    archive_completed_tasks,
    archive_stage_prompts,
    archive_task_file,
)
from task_manager import list_tasks

FRONT_MATTER_DELIMITER = "---"
ALLOWED_MODES = {"readonly", "write_dev", "write_prod"}
DEFAULT_TASK_FILE = os.path.join(TASKS_DIR, "task_current.md")


def load_task_from_file(path: str) -> Tuple[Dict, str]:
    """
    Returns (metadata, body_text) parsed from a task file with YAML front matter.
    If no front matter is present, metadata is an empty dict and body is the full file.
    """
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    lines = content.splitlines()
    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        return {}, content

    end_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONT_MATTER_DELIMITER:
            end_index = idx
            break

    if end_index is None:
        return {}, content

    metadata_text = "\n".join(lines[1:end_index])
    metadata = yaml.safe_load(metadata_text) or {}
    if not isinstance(metadata, dict):
        raise yaml.YAMLError("Front matter must be a mapping.")
    body = "\n".join(lines[end_index + 1:]).strip()
    return metadata, body


class MetaAgent:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.builder = PromptBuilder()
        self.client = CodexClient()

    def _load_config(self, path: str) -> Dict:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return {}

    def _normalize_mode(self, mode: str) -> str:
        if mode in ALLOWED_MODES:
            return mode
        print(f"[WARN] Unsupported mode '{mode}', defaulting to readonly.")
        return "readonly"

    def _resolve_output_path(self, output_path: str | None, task_id: str) -> str:
        if output_path:
            dest = os.path.abspath(output_path)
        else:
            dest = os.path.abspath(os.path.join("output", f"{task_id}_response.md"))

        # Keep outputs inside the Meta-Agent directory for predictability.
        meta_root = os.path.abspath(os.getcwd())
        try:
            common = os.path.commonpath([dest, meta_root])
        except ValueError:
            common = ""

        if common != meta_root:
            print("[WARN] output_path is outside the Meta-Agent directory; redirecting to output/.")
            dest = os.path.abspath(os.path.join("output", os.path.basename(dest)))

        return dest

    def _load_stages(self, path: str = "stages.yaml"):
        if not os.path.exists(path):
            print(f"[ERROR] stages file not found: {path}")
            return []
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or []
        except yaml.YAMLError as exc:
            print(f"[ERROR] Failed to parse stages file: {exc}")
            return []

    def run_stage_pipeline(self) -> bool:
        print("[INFO] Starting stage pipeline from stages.yaml...")
        stages = self._load_stages()
        if not stages:
            print("[WARN] No stages to run.")
            return False

        target_project = self.config.get("project_root") or "."
        for stage in stages:
            name = stage.get("name", "unnamed_stage")
            prompt_file = stage.get("prompt")
            if not prompt_file:
                print(f"[ERROR] Stage {name} is missing a prompt path.")
                return False

            resolved_prompt = os.path.abspath(prompt_file)
            if not os.path.exists(resolved_prompt):
                alternative = os.path.abspath(os.path.join("prompts", prompt_file))
                if os.path.exists(alternative):
                    resolved_prompt = alternative
                else:
                    print(f"[ERROR] Prompt file not found for stage {name}: {prompt_file}")
                    return False

            print(f"[INFO] Running stage: {name} using {prompt_file}")
            try:
                with open(resolved_prompt, "r", encoding="utf-8") as handle:
                    stage_instructions = handle.read()

                print(f"[INFO] Collecting project context from {target_project} for stage {name}...")
                context = ProjectScanner(target_project).collect_project_files()
                print(f"[INFO] Collected project context for stage {name} ({len(context)} chars).")

                full_prompt = self.builder.build_prompt(
                    stage_instructions,
                    context,
                    {"stage": name, "mode": "legacy", "target_project": target_project},
                )

                print(f"[INFO] Sending prompt to Codex for stage {name}...")
                response = self.client.send(full_prompt)
                print(f"[INFO] Codex response received for stage {name}.")

                if isinstance(response, str) and response.lstrip().startswith("[ERROR]"):
                    print(f"[ERROR] Codex call failed for stage {name}: {response}")
                    return False

                FileManager().process_output(response)
                print(f"[INFO] Stage {name} completed.")
            except Exception as exc:
                print(f"[ERROR] Stage {name} failed: {exc}")
                return False

        try:
            print("[INFO] Archiving stage prompts...")
            archive_stage_prompts(stages, target_project=target_project)
            print("[INFO] Archived stage prompts and cleared stages.yaml.")
        except Exception as exc:
            print(f"[WARN] Archiving of stage prompts failed: {exc}")

        return True

    def run_task_file(self, task_path: str) -> bool:
        """
        Legacy wrapper that routes task execution through meta_core.run_task.
        """
        result = run_task(task_path)
        if result.get("status") != "ok":
            print(f"[ERROR] Task {result.get('task_id')} failed: {result.get('error_message')}")
            return False

        print(f"[INFO] Task {result.get('task_id')} completed.")
        if result.get("summary"):
            print(f"[INFO] Summary: {result['summary']}")
        if result.get("changed_files"):
            print(f"[INFO] Changed files ({len(result['changed_files'])}): {', '.join(result['changed_files'])}")
        if result.get("created_files"):
            print(f"[INFO] Created files ({len(result['created_files'])}): {', '.join(result['created_files'])}")
        if result.get("report_md_path"):
            print(f"[INFO] Markdown report: {result['report_md_path']}")
        if result.get("report_json_path"):
            print(f"[INFO] JSON report: {result['report_json_path']}")
        try:
            archive_task_file(os.path.abspath(task_path), target_project=result.get("meta", {}).get("target_project"))
            print(f"[INFO] Archived task file: {task_path}")
        except Exception as exc:
            print(f"[WARN] Failed to archive task file {task_path}: {exc}")
        return True


def parse_args():
    parser = argparse.ArgumentParser(description="Meta-Agent CLI")
    parser.add_argument("--mode", default="auto", help="Execution mode (stages|task) or supervisor cadence (daily|weekly|adhoc|auto).")
    parser.add_argument("--task", dest="task_path", help="Path to a .md task file for task mode.")
    parser.add_argument("--task-id", dest="task_id", help="Task ID to resolve in tasks/<ID>.md for task mode.")
    parser.add_argument("--task-file", dest="task_file", help="Alias for --task (legacy).")
    parser.add_argument("--list-tasks", action="store_true", help="List available tasks from tasks/ directory.")
    parser.add_argument("--project", dest="filter_project", help="Filter tasks by project when listing.")
    parser.add_argument("--task-type", dest="filter_task_type", help="Filter tasks by task type when listing.")
    parser.add_argument("--supervisor-goal", dest="supervisor_goal", help="Run a supervisor goal (high-level string).")
    parser.add_argument("--once", action="store_true", help="Run once and exit (default behavior).")
    parser.add_argument("--encrypt-env", action="store_true", help="Encrypt .env into .env.enc using password 1111.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.encrypt_env:
        try:
            encrypt_env(".env", ".env.enc", "1111")
            print("[INFO] Encrypted .env into .env.enc using password 1111.")
            return 0
        except Exception as exc:
            print(f"[ERROR] Failed to encrypt env: {exc}")
            return 1

    if args.once:
        print("[INFO] --once specified; running a single pass.")

    if args.list_tasks:
        try:
            tasks = list_tasks(project=args.filter_project, task_type=args.filter_task_type)
        except Exception as exc:
            print(f"[ERROR] Failed to list tasks: {exc}")
            return 1
        if not tasks:
            print("No tasks found.")
            return 0
        header = f"{'TASK_ID':30} {'PROJECT':18} {'TYPE':14} TITLE"
        print(header)
        print("-" * len(header))
        for task in tasks:
            print(f"{task.task_id:30} {task.project:18} {task.task_type:14} {task.title}")
        return 0

    if args.supervisor_goal:
        try:
            sup_result = run_supervisor_cycle(
                goal=args.supervisor_goal,
                mode=args.mode or "daily",
                project=args.project or "ai_scalper_bot",
            )
        except Exception as exc:
            print(f"[ERROR] Supervisor run failed: {exc}")
            return 1

        ok_count = sum(1 for r in sup_result.get("tasks", []) if r.get("status") == "ok")
        err_count = sum(1 for r in sup_result.get("tasks", []) if r.get("status") == "error")
        partial_count = sum(1 for r in sup_result.get("tasks", []) if r.get("status") == "partial")

        print("[INFO] Supervisor run completed.")
        print(f"  Goal: {sup_result.get('goal')}")
        print(f"  Mode: {sup_result.get('mode')}")
        print(f"  Project: {sup_result.get('project')}")
        print(f"  Status: {sup_result.get('status')}")
        print(f"  Tasks total: {len(sup_result.get('tasks', []))} (ok/partial/error: {ok_count}/{partial_count}/{err_count})")
        if sup_result.get("supervisor_md_path"):
            print(f"  Summary (MD): {sup_result.get('supervisor_md_path')}")
        if sup_result.get("supervisor_json_path"):
            print(f"  Summary (JSON): {sup_result.get('supervisor_json_path')}")
        if sup_result.get("overall_summary"):
            print(f"  Overall summary: {sup_result.get('overall_summary')}")
        return 0 if sup_result.get("status") == "ok" else 1

    # Resolve task identifier/path if provided
    task_identifier = args.task_path or args.task_file or args.task_id

    allowed_modes = {"auto", "stages", "task"}
    run_mode = args.mode if args.mode in allowed_modes else "auto"
    task_mode = run_mode == "task" or bool(task_identifier)

    try:
        if task_mode:
            if not task_identifier:
                print("[ERROR] Task mode requested but no --task/--task-id provided.")
                return 1
            result = run_task(task_identifier)
            print(f"[INFO] Task {result.get('task_id')} status: {result.get('status')}")
            if result.get("summary"):
                print(f"[INFO] Summary: {result['summary']}")
            if result.get("error_message"):
                print(f"[ERROR] {result['error_message']}")
            if result.get("changed_files"):
                print(f"[INFO] Changed files ({len(result['changed_files'])}): {', '.join(result['changed_files'])}")
            if result.get("created_files"):
                print(f"[INFO] Created files ({len(result['created_files'])}): {', '.join(result['created_files'])}")
            if result.get("report_md_path"):
                print(f"[INFO] Markdown report: {result['report_md_path']}")
            if result.get("report_json_path"):
                print(f"[INFO] JSON report: {result['report_json_path']}")
            return 0 if result.get("status") == "ok" else 1

        agent = MetaAgent()
        success = agent.run_stage_pipeline()
    except Exception as exc:
        print(f"[ERROR] Meta-Agent failed: {exc}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
