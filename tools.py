from pathlib import Path
import subprocess


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
    path = Path(args.strip())
    try:
        path.touch()
        return f"Created file at {path}"
    except Exception as e:
        return str(e)


tools = {
    "list_files": {"description": "lists files (first and only argument is the directory)", "function": list_files},
    "create_directory": {"description": "creates a directory (first and only argument is the directory)", "function": create_directory},
    "read_file": {"description": "outputs the text contents of a file (first and only argument is the file path)", "function": read_file},
    "write_file": {"description": "overwrites a file with specified contents. arguments: path, then newline, then all of the contents (don't escape anything)", "function": write_file},
    "run_command": {"description": "runs a shell command. arguments: newline-separated arguments for the command (the first 'argument' is the command itself)", "function": run_command},
}
