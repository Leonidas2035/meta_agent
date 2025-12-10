import os
from dataclasses import dataclass
from typing import Dict, Optional

import yaml

from paths import BASE_DIR

DEFAULT_PROJECTS_PATH = os.path.join(BASE_DIR, "config", "projects.yaml")


@dataclass
class ProjectInfo:
    project_id: str
    root_path: str  # absolute path


@dataclass
class ProjectRegistry:
    default_project_id: str
    projects: Dict[str, ProjectInfo]

    def get(self, project_id: Optional[str]) -> Optional[ProjectInfo]:
        if not project_id:
            return self.projects.get(self.default_project_id)
        return self.projects.get(project_id)


def _ensure_default_config(path: str = DEFAULT_PROJECTS_PATH) -> None:
    """
    Writes a simple default config if none exists, to keep the system usable out of the box.
    """
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    default_yaml = {
        "default": "ai_scalper_bot",
        "projects": {
            "ai_scalper_bot": {"path": "../ai_scalper_bot"},
            "meta_agent": {"path": "."},
            "supervisor_agent": {"path": "../Supervisor agent"},
        },
    }
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(default_yaml, handle, allow_unicode=True, sort_keys=False)


def load_project_registry(config_path: str = DEFAULT_PROJECTS_PATH) -> ProjectRegistry:
    """
    Reads config/projects.yaml, resolves relative paths against BASE_DIR, and returns a registry.
    If the file is missing, a default config is created automatically.
    """
    _ensure_default_config(config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Failed to parse project registry: {exc}")
    except OSError as exc:
        raise RuntimeError(f"Failed to read project registry: {exc}")

    default_project_id = raw.get("default") or "ai_scalper_bot"
    projects_map = raw.get("projects") or {}
    projects: Dict[str, ProjectInfo] = {}

    for pid, info in projects_map.items():
        rel_path = info.get("path")
        if not rel_path:
            continue
        abs_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
        projects[pid] = ProjectInfo(project_id=pid, root_path=abs_path)

    if default_project_id not in projects:
        raise RuntimeError(f"Default project_id '{default_project_id}' not found in registry projects.")

    return ProjectRegistry(default_project_id=default_project_id, projects=projects)


def resolve_project_root(project_id: Optional[str], registry: ProjectRegistry) -> ProjectInfo:
    """
    Resolves a project_id to ProjectInfo, using default when None. Raises on unknown id.
    """
    info = registry.get(project_id)
    if not info:
        raise KeyError(f"Unknown project id '{project_id}'. Available: {', '.join(registry.projects.keys())}")
    return info
