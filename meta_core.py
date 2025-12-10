import json
import os
from datetime import datetime
from typing import Dict, List

from codex_client import CodexClient
from file_manager import FileManager
from project_scanner import ProjectScanner
from prompt_builder import PromptBuilder
from report_schema import Report, write_json_report, write_md_report
from task_manager import load_task
from task_schema import TaskParseError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
TASKS_DIR = os.path.join(BASE_DIR, "tasks")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _load_config(path: str = CONFIG_PATH) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def _build_summary(status: str, changed_files: List[str], created_files: List[str], error_message: str | None) -> str:
    if status != "ok":
        return f"Task failed: {error_message}" if error_message else "Task failed."
    touched = list(dict.fromkeys(created_files + changed_files))
    if not touched:
        return "Model responded without file changes."
    if len(touched) <= 3:
        return f"Updated files: {', '.join(touched)}"
    return f"Updated {len(touched)} files."


def _resolve_target_project(task_project: str) -> str:
    """
    Resolves the absolute target project path.
    If the task_project is absolute, use it. Otherwise, fall back to config project_root or current dir.
    """
    if os.path.isabs(task_project):
        return task_project
    config = _load_config()
    project_root = config.get("project_root")
    if project_root and os.path.exists(project_root):
        return project_root
    return os.path.abspath(task_project)


def run_task(task_id_or_path: str) -> Dict:
    """
    Executes a single task (by TASK_ID or path) through Meta-Agent pipeline.

    Steps:
      1) Load Task via task_manager.load_task.
      2) Build prompt using Task body and metadata.
      3) Call Codex model once.
      4) Apply file changes using FileManager.
      5) Build a Report and write JSON/MD outputs.
      6) Return a dict with key report fields for Supervisor.
    """
    _ensure_dir(TASKS_DIR)
    _ensure_dir(REPORTS_DIR)

    started_at = datetime.utcnow().isoformat() + "Z"
    finished_at: str | None = None
    model_name: str | None = None

    report: Report | None = None
    json_path = None
    md_path = None

    try:
        task = load_task(task_id_or_path)
        target_project = _resolve_target_project(task.project)

        prompt_metadata = {
            "task_id": task.task_id,
            "project": task.project,
            "task_type": task.task_type,
            "title": task.title,
            "priority": task.priority,
            "source": task.source,
            "target_project": target_project,
            "run_mode": "task",
        }

        context = ProjectScanner(target_project).collect_project_files()
        full_prompt = PromptBuilder().build_prompt(task.body_markdown, context, prompt_metadata)

        client = CodexClient()
        model_name = client.model
        response = client.send(full_prompt)

        if isinstance(response, str) and response.lstrip().startswith("[ERROR]"):
            raise RuntimeError(response)

        manager = FileManager(target_project=target_project, mode="write_dev")
        file_changes = manager.process_output(response)

        finished_at = datetime.utcnow().isoformat() + "Z"
        report = Report(
            task_id=task.task_id,
            project=task.project,
            task_type=task.task_type,
            title=task.title,
            priority=task.priority,
            status="ok",
            error_message=None,
            summary=_build_summary("ok", file_changes.get("changed_files", []), file_changes.get("created_files", []), None),
            changed_files=file_changes.get("changed_files", []),
            created_files=file_changes.get("created_files", []),
            deleted_files=[],
            meta={
                "started_at": started_at,
                "finished_at": finished_at,
                "model": model_name,
                "source": task.source,
                "task_path": task.path,
                "target_project": target_project,
                "task_type": task.task_type,
                "priority": task.priority,
            },
        )
    except (TaskParseError, FileNotFoundError) as exc:
        finished_at = datetime.utcnow().isoformat() + "Z"
        report = Report(
            task_id=getattr(exc, "task_id", task_id_or_path),
            project="unknown",
            task_type="unknown",
            title="",
            priority="normal",
            status="error",
            error_message=str(exc),
            summary=_build_summary("error", [], [], str(exc)),
            changed_files=[],
            created_files=[],
            deleted_files=[],
            meta={
                "started_at": started_at,
                "finished_at": finished_at,
                "model": model_name,
                "source": "unknown",
                "task_path": task_id_or_path,
            },
        )
    except Exception as exc:
        finished_at = datetime.utcnow().isoformat() + "Z"
        # We may not have loaded task successfully; fill safe defaults.
        report = Report(
            task_id=getattr(exc, "task_id", str(task_id_or_path)),
            project=getattr(locals().get("task", None), "project", "unknown"),
            task_type=getattr(locals().get("task", None), "task_type", "unknown"),
            title=getattr(locals().get("task", None), "title", ""),
            priority=getattr(locals().get("task", None), "priority", "normal"),
            status="error",
            error_message=str(exc),
            summary=_build_summary("error", [], [], str(exc)),
            changed_files=[],
            created_files=[],
            deleted_files=[],
            meta={
                "started_at": started_at,
                "finished_at": finished_at,
                "model": model_name,
                "source": getattr(locals().get("task", None), "source", "unknown"),
                "task_path": getattr(locals().get("task", None), "path", task_id_or_path),
            },
        )
    finally:
        if report is not None:
            finished = finished_at or datetime.utcnow().isoformat() + "Z"
            report.meta.setdefault("finished_at", finished)
            report.meta.setdefault("started_at", started_at)
            try:
                started_dt = datetime.fromisoformat(report.meta["started_at"].replace("Z", "+00:00"))
                finished_dt = datetime.fromisoformat(report.meta["finished_at"].replace("Z", "+00:00"))
                duration_sec = max((finished_dt - started_dt).total_seconds(), 0)
                report.meta["duration_sec"] = duration_sec
            except Exception:
                pass

            json_path = write_json_report(report)
            md_path = write_md_report(report)

    # Return compact dict for Supervisor
    return {
        "task_id": report.task_id if report else task_id_or_path,
        "project": report.project if report else "unknown",
        "task_type": report.task_type if report else "unknown",
        "title": report.title if report else "",
        "priority": report.priority if report else "normal",
        "status": report.status if report else "error",
        "error_message": report.error_message if report else "unknown error",
        "changed_files": report.changed_files if report else [],
        "created_files": report.created_files if report else [],
        "deleted_files": report.deleted_files if report else [],
        "summary": report.summary if report else "",
        "risks": report.risks if report else [],
        "notes": report.notes if report else [],
        "meta": report.meta if report else {},
        "report_json_path": json_path,
        "report_md_path": md_path,
    }
