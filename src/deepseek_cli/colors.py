# ANSI color codes for terminal output

class Colors:
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\033[37m'

def colorize(text, color):
    return f"{color}{text}{Colors.RESET}"

def print_color(text, color):
    print(colorize(text, color))