from tools.file_tools import read_file_tool, list_files_tool, edit_file_tool

TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool
}
