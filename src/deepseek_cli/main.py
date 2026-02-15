import os
import argparse
from deepseek_api import DeepSeekAPI, POWSolver
from .tools import tools
import platformdirs
from dotenv import load_dotenv
from .colors import Colors


def main():
    config_dir = platformdirs.user_config_dir("deepseek")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='DeepSeek CLI chat')
    parser.add_argument('--chat', '-c', help='Resume an existing chat by ID')
    parser.add_argument(
        '--wasm', '-w', help='Path to the WASM file for PoW solving', default=None)
    parser.add_argument(
        '--config', help='Path to config directory', default=config_dir)
    args = parser.parse_args()

    config_path = os.path.join(config_dir, "env")
    load_dotenv(config_path)
    token = os.getenv('TOKEN', None)
    if token is None:
        print(f"""{Colors.YELLOW}no TOKEN env var found
specify TOKEN=xxx in {config_path}
you can obtain the token by copying the authorization header's value (without 'Bearer') from a request to DeepSeek in your browser
{Colors.RESET}""")

        exit(1)

    pow_solver = POWSolver(args.wasm)
    api = DeepSeekAPI(token, pow_solver)

    if args.chat:
        # Resume existing chat
        chat = {"id": args.chat}
        first_prompt = False
        print(f"{Colors.MAGENTA}Resuming chat {args.chat}{Colors.RESET}")
        # Fetch the latest message ID to continue the thread
        try:
            chat_info = api.get_chat_info(args.chat)
            message = {"message_id": chat_info.get("current_message_id")}
            if message["message_id"]:
                print(
                    f"{Colors.MAGENTA}Latest message ID: {message['message_id']}{Colors.RESET}")
            else:
                print(f"{Colors.MAGENTA}No previous messages found, starting fresh.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not fetch chat info: {e}{Colors.RESET}")
            message = {}
    else:
        # Create new chat
        chat = api.create_chat()
        first_prompt = True
        message = {}
        print(f"{Colors.MAGENTA}Created new chat with ID: {chat['id']}{Colors.RESET}")

    system_prompt = f"""System prompt:
You are an AI assistant inside a CLI application. You are not in a "simulation", you are running on a real system. You can use tools to interact with it.
To show output to the user (or ask questions), simply print the output normally, no tools will be called.
To invoke a tool, output it's exact name, a newline, and it's arguments.
If you need to make multiple tool calls in one response, separate each tool call with a line containing exactly "###" (three hash symbols). Also include '###' between tool calls and your own output. For example:

Output for user...
###
tool_name1
arguments for tool 1...
###
tool_name2
arguments for tool 2...
###
More output for user...

If the user provides no context, assume they're talking about the current directory. Don't assume contents of files, read them first.

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
                prompt = input(f"{Colors.MAGENTA}> {Colors.RESET}")
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
                    print(f"{Colors.BLUE}Reasoning:{Colors.RESET}")
                    printed_thinking_header = True
                print(f"{Colors.CYAN}{chunk['content']}{Colors.RESET}", end="", flush=True)
                full_thinking += chunk["content"]
            elif chunk["type"] == "content":
                if not printed_output_header:
                    if full_thinking:
                        print()  # newline after reasoning
                    print(f"{Colors.BLUE}Output:{Colors.RESET}")
                    printed_output_header = True
                print(f"{Colors.WHITE}{chunk['content']}{Colors.RESET}", end="", flush=True)
                full_content += chunk["content"]
            elif chunk["type"] == "message":
                message = chunk["content"]
        print()  # final newline

        # Tool invocation detection - support multiple calls separated by "###"
        tool_calls = []
        # Split the content by "###" delimiter
        segments = full_content.split('###')
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            # Each segment should have tool name on first line, then args
            lines = segment.split('\n', 1)
            tool_name = lines[0].strip()
            if not tool_name:
                continue
            if tool_name in tools:
                args = lines[1] if len(lines) > 1 else ''
                tool_calls.append((tool_name, args))

        if not tool_calls:
            # No valid tool call found
            prompt = None
            continue

        # Execute tool calls sequentially
        results = []
        for i, call in enumerate(tool_calls, 1):
            if len(call) == 3:  # error case
                tool_name, _, error_msg = call
                print(f"{Colors.YELLOW}Skipping invalid tool call {i}: {tool_name}{Colors.RESET}")
                results.append(f"Tool call {i}: {error_msg}")
                continue
            tool_name, args = call
            print(f"{Colors.YELLOW}Calling tool {tool_name} ({i}/{len(tool_calls)}){Colors.RESET}")
            try:
                result = tools[tool_name]["function"](args)
                results.append(f"Tool call {i}: {tool_name} returned:\n{result}")
            except Exception as e:
                results.append(f"Tool call {i}: {tool_name} failed:\n{e}")

        # Combine results into a single prompt
        prompt = "\n\n".join(results)
