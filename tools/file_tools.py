import chardet
from typing import Any, Dict
from utils import resolve_abs_path

def read_file_tool(filename: str) -> Dict[str, Any]:
    full_path = resolve_abs_path(filename)

    if not full_path.is_file():
        return {"error": "File not found or is a directory"}

    try:
        with open(full_path, "rb") as f:
            raw_data = f.read()

        detected = chardet.detect(raw_data)
        encoding = detected["encoding"] or "utf-8"

        content = raw_data.decode(encoding, errors="replace")

    except Exception as e:
        return {"error": str(e)}

    return {
        "file_path": str(full_path),
        "encoding_used": encoding,
        "content": content
    }


def list_files_tool(path: str) -> Dict[str, Any]:
    full_path = resolve_abs_path(path)

    all_files = []
    for item in full_path.iterdir():
        all_files.append({
            "filename": item.name,
            "type": "file" if item.is_file() else "dir"
        })

    return {"path": str(full_path), "files": all_files}


def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    full_path = resolve_abs_path(path)

    if old_str == "":
        full_path.write_text(new_str, encoding="utf-8")
        return {"path": str(full_path), "action": "created_file"}

    original = full_path.read_text(encoding="utf-8")

    if original.find(old_str) == -1:
        return {"path": str(full_path), "action": "old_str not found"}

    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")

    return {"path": str(full_path), "action": "edited"}

