import os
from pathlib import Path


def load_project_env(start = None):
    """
    Load the first nearby .env file without overwriting existing variables.
    input: start str/path类
    """
    roots: list[Path] = []
    if start is not None:
        roots.append(Path(start).resolve())
    roots.extend([Path.cwd().resolve(), Path(__file__).resolve().parent])

    seen: set[Path] = set()
    for root in roots:
        if root.is_file():
            root = root.parent
        for env_path in (root / ".env", root.parent / ".env", root.parent / "tarot_project" / ".env"):
            if env_path in seen:
                continue
            seen.add(env_path)
            if env_path.exists():
                _load_env_file(env_path)
                return


def _load_env_file(path):
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
