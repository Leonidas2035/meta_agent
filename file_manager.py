import os
import re


class FileManager:
    FILE_PATTERN = r"===FILE:\s*(.*?)===\n(.*?)(?=\n===FILE:|$)"

    def __init__(self, base_output_dir: str = "output", target_project: str | None = None, mode: str = "write_dev"):
        self.base_output_dir = os.path.abspath(base_output_dir)
        self.target_project = os.path.abspath(target_project) if target_project else None
        self.mode = mode

    def _ensure_dir(self, path: str) -> None:
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)

    def _resolve_destination(self, declared_path: str) -> str:
        normalized = os.path.normpath(declared_path.strip())

        # Redirect everything to output when in readonly mode.
        if self.mode == "readonly" or not self.target_project:
            return os.path.join(self.base_output_dir, normalized.lstrip("/\\"))

        if os.path.isabs(normalized):
            abs_path = os.path.abspath(normalized)
            try:
                common = os.path.commonpath([abs_path, self.target_project])
            except ValueError:
                common = ""
            if common == self.target_project:
                return abs_path
            # Outside the target project, so redirect to output for safety.
            safe_name = normalized.lstrip("\\/").replace(":", "")
            return os.path.join(self.base_output_dir, safe_name)

        return os.path.join(self.target_project, normalized)

    def _display_path(self, destination: str) -> str:
        """
        Returns a readable path, preferring project-relative paths when possible.
        """
        abs_dest = os.path.abspath(destination)

        if self.target_project:
            target_root = os.path.abspath(self.target_project)
            try:
                common = os.path.commonpath([abs_dest, target_root])
            except ValueError:
                common = ""
            if common == target_root:
                return os.path.relpath(abs_dest, target_root)

        try:
            common_output = os.path.commonpath([abs_dest, self.base_output_dir])
        except ValueError:
            common_output = ""
        if common_output == self.base_output_dir:
            return os.path.relpath(abs_dest, self.base_output_dir)

        return abs_dest

    def process_output(self, response: str) -> dict:
        """
        Writes files from the model response and returns file change info.

        Returns:
            {
                "written_files": [...],   # all files touched
                "created_files": [...],   # files that did not exist before
                "changed_files": [...],   # files that already existed
            }
        """
        written_files: list[str] = []
        created_files: list[str] = []
        changed_files: list[str] = []

        matches = re.findall(self.FILE_PATTERN, response, flags=re.S | re.M)
        for path, code in matches:
            dest = self._resolve_destination(path)
            existed_before = os.path.exists(dest)
            self._ensure_dir(dest)
            with open(dest, "w", encoding="utf-8") as handle:
                handle.write(code)

            display_path = self._display_path(dest)
            if display_path not in written_files:
                written_files.append(display_path)
            if existed_before:
                if display_path not in changed_files:
                    changed_files.append(display_path)
            else:
                if display_path not in created_files:
                    created_files.append(display_path)

            print(f"[WRITE] Created/updated: {dest}")

        return {
            "written_files": written_files,
            "created_files": created_files,
            "changed_files": changed_files,
        }

    def write_raw_output(self, content: str, output_path: str) -> str:
        """
        Writes raw content to a specific path (usually from metadata.output_path).
        Returns the absolute path written.
        """
        dest = os.path.abspath(output_path)
        self._ensure_dir(dest)
        with open(dest, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"[WRITE] Saved response to: {dest}")
        return dest
