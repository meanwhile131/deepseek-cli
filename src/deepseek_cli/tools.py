from pathlib import Path
import subprocess
import shutil
import os


def list_files(args: str):
    path = Path(args.strip())
    dirs = map(str, list(path.iterdir()))
    return '\n'.join(dirs)


def create_directory(args: str):
    path = Path(args.strip())
    path.mkdir(parents=True)
    return f"Created directory at {path}"


def write_file(args: str):
    newline_idx = args.index('\n')
    path = Path(args[:newline_idx])
    contents = args[newline_idx+1:]
    path.touch(exist_ok=True)
    path.write_text(contents)
    return f"Written to {path}"


def read_file(args: str):
    path = Path(args.strip())
    return path.read_text()


def run_command(args: str):
    command_args = args.splitlines()
    cmd = subprocess.run(
        command_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return f"""{cmd.stdout.decode()}

The command exited with code {cmd.returncode}"""


def find_replace(args: str):
    lines = args.splitlines()
    path = Path(lines[0].strip())
    find = lines[1]
    replace = '\n'.join(lines[2:])
    content = path.read_text()
    new_content = content.replace(find, replace)
    path.write_text(new_content)
    return f"Replaced {content.count(find)} entries"


def file_exists(args: str):
    path = Path(args.strip())
    return str(path.exists())


def append_file(args: str):
    newline_idx = args.index('\n')
    path = Path(args[:newline_idx])
    content = args[newline_idx+1:]
    with open(path, 'a') as f:
        f.write(content)
    return f"Appended to {path}"


def delete_file(args: str):
    path = Path(args.strip())
    if path.is_file():
        path.unlink()
        return f"Deleted file {path}"
    elif path.is_dir():
        shutil.rmtree(path)
        return f"Deleted directory {path} (recursively)"
    else:
        return f"Path does not exist: {path}"


def copy_file(args: str):
    lines = args.splitlines()
    src = Path(lines[0].strip())
    dst = Path(lines[1].strip())
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return f"Copied {src} to {dst}"


def move_file(args: str):
    lines = args.splitlines()
    src = Path(lines[0].strip())
    dst = Path(lines[1].strip())
    shutil.move(src, dst)
    return f"Moved {src} to {dst}"


def get_cwd(args: str):
    return os.getcwd()


def apply_search_replace(args: str):
    lines = args.splitlines()
    if not lines:
        return "Error: No arguments provided"
    path = Path(lines[0].strip())
    block = '\n'.join(lines[1:])
    search_marker = '<<<<<<< SEARCH'
    sep_marker = '======='
    replace_marker = '>>>>>>> REPLACE'
    search_start = block.find(search_marker)
    if search_start == -1:
        return "Error: Could not find <<<<<<< SEARCH marker"
    sep_start = block.find(sep_marker, search_start + len(search_marker))
    if sep_start == -1:
        return "Error: Could not find ======= marker"
    replace_end = block.find(replace_marker, sep_start + len(sep_marker))
    if replace_end == -1:
        return "Error: Could not find >>>>>>> REPLACE marker"
    search_content = block[search_start +
                           len(search_marker):sep_start].strip('\n')
    replace_content = block[sep_start +
                            len(sep_marker):replace_end].strip('\n')
    content = path.read_text()
    new_content = content.replace(search_content, replace_content)
    if new_content == content:
        return "Error: Search string not found in file"
    count = content.count(search_content)
    path.write_text(new_content)
    return f"Replaced {count} occurrence(s) in {path}"


tools = {
    "list_files": {"description": "lists files (first and only argument is the directory)", "function": list_files},
    "create_directory": {"description": "creates a directory (first and only argument is the directory)", "function": create_directory},
    "read_file": {"description": "outputs the text contents of a file (first and only argument is the file path)", "function": read_file},
    "apply_search_replace": {"description": "applies a search/replace block to a file. prefer this over write_file for small changes. arguments: file path, then newline, then the block with <<<<<<< SEARCH and >>>>>>> REPLACE markers", "function": apply_search_replace},
    "write_file": {"description": "overwrites a file with specified contents. arguments: path, then newline, then all of the contents (don't escape anything)", "function": write_file},
    "run_command": {"description": "runs a shell command. arguments: newline-separated arguments for the command (the first 'argument' is the command itself)", "function": run_command},
    "find_replace": {"description": "replaces occurrences of a string in a file. arguments: path, then newline, then find (must be a single line, no newline), then newline, then replace (may contain newlines)", "function": find_replace},
    "file_exists": {"description": "checks if a file or directory exists. argument: path", "function": file_exists},
    "append_file": {"description": "appends content to a file. arguments: path, then newline, then content to append", "function": append_file},
    "delete_file": {"description": "deletes a file or directory (recursive). argument: path", "function": delete_file},
    "copy_file": {"description": "copies a file or directory. arguments: source, then newline, then destination", "function": copy_file},
    "move_file": {"description": "moves/renames a file or directory. arguments: source, then newline, then destination", "function": move_file},
    "get_cwd": {"description": "returns the current working directory. must be followed by a newline. no other arguments are needed.", "function": get_cwd},
}
