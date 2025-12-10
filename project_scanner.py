import os
from typing import Iterable


class ProjectScanner:
    def __init__(self, target_dir: str = ".", include_ext: Iterable[str] | None = None):
        self.target = target_dir
        self.include_ext = tuple(include_ext) if include_ext else (".py", ".yaml", ".json", ".md")

    def collect_project_files(self, target_dir: str | None = None) -> str:
        """
        Recursively loads project files into a single string with file markers.
        Only reads text files with allowed extensions to avoid noisy dumps.
        """
        base_dir = target_dir or self.target
        if not os.path.isdir(base_dir):
            return ""

        result = ""
        for root, _, files in os.walk(base_dir):
            for filename in files:
                if not filename.endswith(self.include_ext):
                    continue
                path = os.path.join(root, filename)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fd:
                        code = fd.read()
                except OSError:
                    continue
                rel = os.path.relpath(path, base_dir)
                result += f"\n===FILE: {rel}===\n{code}\n"
        return result
