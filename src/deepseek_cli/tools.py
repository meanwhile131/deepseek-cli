from pathlib import Path
import subprocess
from .colors import Colors, print_color


def list_files(args: str):
    path = Path(args.strip())
    dirs = map(str, list(path.iterdir()))
    return '\n'.join(dirs)


def create_directory(args: str):
    path = Path(args.strip())
    path.mkdir(parents=True)
    return f"Created directory at {path}"


def read_file(args: str):
    path = Path(args.strip())
    return path.read_text()


def run_command(args: str):
    command_args = args.splitlines()
    # Print command in cyan
    print_color("Running command: " + " ".join(command_args), Colors.CYAN)
    cmd = subprocess.run(
        command_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = cmd.stdout.decode()
    # Print output in yellow
    if output:
        print_color(output, Colors.YELLOW)
    # Print exit code
    if cmd.returncode == 0:
        print_color(f"Command exited with code {cmd.returncode}", Colors.GREEN)
    else:
        print_color(f"Command exited with code {cmd.returncode}", Colors.FAIL)
    return f"""{output}

The command exited with code {cmd.returncode}"""


def apply_search_replace(args: str):
    lines = args.splitlines()
    if not lines:
        return "Error: No arguments provided"
    path = Path(lines[0].strip())
    path.touch()
    block_lines = lines[1:]  # the rest are the block

    search_marker = '<<<<<<< SEARCH'
    sep_marker = '======='
    replace_marker = '>>>>>>> REPLACE'

    # Find indices of marker lines
    search_idx = None
    sep_idx = None
    replace_idx = None
    for i, line in enumerate(block_lines):
        stripped = line.rstrip('\n')
        if stripped == search_marker and search_idx is None:
            search_idx = i
        elif stripped == sep_marker and search_idx is not None and sep_idx is None:
            sep_idx = i
        elif stripped == replace_marker and sep_idx is not None and replace_idx is None:
            replace_idx = i
            break

    if search_idx is None:
        return "Error: Could not find <<<<<<< SEARCH marker line"
    if sep_idx is None:
        return "Error: Could not find ======= marker line"
    if replace_idx is None:
        return "Error: Could not find >>>>>>> REPLACE marker line"

    # Extract search content (lines between search and sep, excluding markers)
    search_lines = block_lines[search_idx+1:sep_idx]
    replace_lines = block_lines[sep_idx+1:replace_idx]

    # Preserve newlines by joining with newline
    search_content = '\n'.join(search_lines)
    replace_content = '\n'.join(replace_lines)

    content = path.read_text()
    new_content = content.replace(search_content, replace_content)
    if new_content == content:
        return "Error: Search string not found in file"
    count = content.count(search_content)
    path.write_text(new_content)
    return f"Replaced {count} occurrence(s) in {path}"


tools = {
    "list_files": {"description": "lists files recursively (first and only argument is the directory)", "function": list_files},
    "create_directory": {"description": "creates a directory (first and only argument is the directory)", "function": create_directory},
    "read_file": {"description": "outputs the text contents of a file (first and only argument is the file path)", "function": read_file},
    "run_command": {"description": "runs a shell command. arguments: newline-separated arguments for the command (the first 'argument' is the command itself)", "function": run_command},
    "apply_search_replace": {"description": "applies a search/replace block to a file. will create the file if it doesn't exist. arguments: file path, then newline, then the block with <<<<<<< SEARCH, =======, and >>>>>>> REPLACE markers", "function": apply_search_replace},
}
