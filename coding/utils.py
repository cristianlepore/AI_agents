from pathlib import Path

BASE_DIR = Path.cwd()

def resolve_abs_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()

    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()

    return path
