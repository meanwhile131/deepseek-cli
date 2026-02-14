import os
import argparse
from pow_solve import POWSolver
from api import DeepSeekAPI
from tools import tools

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
BLUE = "\033[34m"
WHITE = "\033[37m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"

# Parse command-line arguments
parser = argparse.ArgumentParser(description='DeepSeek CLI chat')
parser.add_argument('--chat', '-c', help='Resume an existing chat by ID')
parser.add_argument('--wasm', '-w', help='Path to the WASM file for PoW solving', default='sha3_wasm_bg.7b9ca65ddd.wasm')
args = parser.parse_args()

token = os.getenv('TOKEN', None)
if token is None:
    print(f"{YELLOW}no TOKEN env var found{RESET}")
    exit(1)

pow_solver = POWSolver(args.wasm)
api = DeepSeekAPI(token, pow_solver)

if args.chat:
    # Resume existing chat
    chat = {"id": args.chat}
    first_prompt = False
    print(f"{MAGENTA}Resuming chat {args.chat}{RESET}")
    # Fetch the latest message ID to continue the thread
    try:
        chat_info = api.get_chat_info(args.chat)
        message = {"message_id": chat_info.get("current_message_id")}
        if message["message_id"]:
            print(f"{MAGENTA}Latest message ID: {message['message_id']}{RESET}")
        else:
            print(f"{MAGENTA}No previous messages found, starting fresh.{RESET}")
    except Exception as e:
        print(f"{YELLOW}Warning: Could not fetch chat info: {e}{RESET}")
        message = {}
else:
    # Create new chat
    chat = api.create_chat()
    first_prompt = True
    message = {}
    print(f"{MAGENTA}Created new chat with ID: {chat['id']}{RESET}")

system_prompt = f"""System prompt:
You are an AI assistant inside a CLI application. To invoke a tool, output ONLY it's exact name, a newline, and it's arguments. You may only make one tool call per message. To not invoke any tools, simply output text normally. There must be no output after or before this.
If the user provides no context, assume they're talking about the current directory.

Available tools:
"""
for tool in tools:
    system_prompt += f"{tool}: {tools[tool]['description']}\n"
system_prompt += f"""
User prompt:
"""
prompt = None
while True:
    if prompt is None:
        try:
            prompt = input(f"{MAGENTA}> {RESET}")
        except EOFError:
            break
    if first_prompt:
        prompt = system_prompt + prompt
        first_prompt = False

    # Stream the response
    stream = api.complete_stream(
        chat["id"],
        prompt,
        parent_message_id=message.get("message_id"),
        thinking=True,
        search=True
    )

    full_thinking = ""
    full_content = ""
    printed_thinking_header = False
    printed_output_header = False

    for chunk in stream:
        if chunk["type"] == "thinking":
            if not printed_thinking_header:
                print(f"{BLUE}Reasoning:{RESET}")
                printed_thinking_header = True
            print(f"{CYAN}{chunk['content']}{RESET}", end="", flush=True)
            full_thinking += chunk["content"]
        elif chunk["type"] == "content":
            if not printed_output_header:
                if full_thinking:
                    print()  # newline after reasoning
                print(f"{BLUE}Output:{RESET}")
                printed_output_header = True
            print(f"{WHITE}{chunk['content']}{RESET}", end="", flush=True)
            full_content += chunk["content"]
        elif chunk["type"] == "message":
            message = chunk["content"]
    print()  # final newline

    # Tool invocation detection
    selected_tool = None
    try:
        first_newline_idx = full_content.index('\n')
        tool = full_content[:first_newline_idx]
        if tool in tools:
            selected_tool = tool
    except ValueError:
        pass

    if selected_tool is None:
        # No tool call, wait for next user input
        prompt = None
        continue

    print(f"{YELLOW}Calling tool {selected_tool}{RESET}")
    try:
        args = full_content[first_newline_idx + 1:]
        result = tools[selected_tool]["function"](args)
        prompt = f"Tool {selected_tool} returned:\n{result}"
    except Exception as e:
        prompt = f"Tool {selected_tool} failed:\n{e}"