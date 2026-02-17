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
    path.touch()  # create file if it doesn't exist
    block_lines = lines[1:]  # remaining lines contain one or more blocks

    search_marker = '<<<<<<< SEARCH'
    sep_marker = '======='
    replace_marker = '>>>>>>> REPLACE'

    # Read current file content
    content = path.read_text()
    current_content = content
    total_replacements = 0
    block_count = 0
    errors = []

    i = 0
    while i < len(block_lines):
        # Find the next block's markers
        try:
            # Locate SEARCH marker
            search_idx = block_lines.index(search_marker, i)
            # Locate SEP marker after that
            sep_idx = block_lines.index(sep_marker, search_idx + 1)
            # Locate REPLACE marker after that
            replace_idx = block_lines.index(replace_marker, sep_idx + 1)
        except ValueError:
            errors.append(f"Block starting at line {i+2} is malformed (missing markers)")
            # Skip to next line to avoid infinite loop
            i += 1
            continue

        # Extract search and replace content (lines between markers, excluding markers)
        search_lines = block_lines[search_idx+1:sep_idx]
        replace_lines = block_lines[sep_idx+1:replace_idx]
        search_content = '\n'.join(search_lines)
        replace_content = '\n'.join(replace_lines)

        # Apply replacement to current content
        if search_content not in current_content:
            errors.append(f"Block {block_count+1}: Search string not found in current content")
        else:
            count = current_content.count(search_content)
            current_content = current_content.replace(search_content, replace_content)
            total_replacements += count
            block_count += 1

        # Move past this block
        i = replace_idx + 1

    # Write final content back to file
    path.write_text(current_content)

    # Build result message
    result = f"Applied {block_count} block(s) with {total_replacements} total replacement(s) in {path}"
    if errors:
        result += "\nErrors:\n" + "\n".join(errors)
    return result


tools = {
    "list_files": {"description": "lists files recursively (first and only argument is the directory)", "function": list_files},
    "create_directory": {"description": "creates a directory (first and only argument is the directory)", "function": create_directory},
    "read_file": {"description": "outputs the text contents of a file (first and only argument is the file path)", "function": read_file},
    "run_command": {"description": "runs a shell command. arguments: newline-separated arguments for the command (the first 'argument' is the command itself)", "function": run_command},
    "apply_search_replace": {"description": "applies one or more search/replace blocks to a file. Will create the file if it doesn't exist. Arguments: file path, then newline, then the block(s) with <<<<<<< SEARCH, =======, and >>>>>>> REPLACE markers. Multiple blocks can be concatenated; each will be applied sequentially to the current file content.", "function": apply_search_replace},
}
