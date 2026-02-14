import os

def list_files(path: str):
    return '\n'.join(os.listdir(path))

tools = {
    "list_files": {"description": "lists files (first argument is the directory)", "function": list_files}
}
