import os
from pow_solve import POWSolver
from api import DeepSeekAPI
from tools import tools

token = os.getenv('TOKEN', None)
if token is None:
    print("no TOKEN env var found")
    exit(1)

pow_solver = POWSolver("sha3_wasm_bg.7b9ca65ddd.wasm")
api = DeepSeekAPI(token, pow_solver)
chat = api.create_chat()
message = {}
system_prompt = """System prompt:
You are an AI assistant inside a CLI application. To invoke a tool, output ONLY it's exact name, a newline, and it's arguments. You may only make one tool call per message. To not invoke any tools, simply output text normally. There must be no output after or before this. Available tools:
"""
for tool in tools:
    system_prompt += f"{tool}: {tools[tool]["description"]}\n"
system_prompt += """
User prompt:
"""
first_prompt = True
prompt = None
while True:
    if prompt is None:
        try:
            prompt = input("\033[1m>\033[0m ")
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
                print("\033[1mReasoning:\033[0m")
                printed_thinking_header = True
            print(chunk["content"], end="", flush=True)
            full_thinking += chunk["content"]
        elif chunk["type"] == "content":
            if not printed_output_header:
                if full_thinking:
                    print()  # newline after reasoning
                print("\033[1mOutput:\033[0m")
                printed_output_header = True
            print(chunk["content"], end="", flush=True)
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

    print(f"\033[1mCalling tool {selected_tool}\033[0m")
    try:
        args = full_content[first_newline_idx + 1:]
        result = tools[selected_tool]["function"](args)
        prompt = f"Tool {selected_tool} returned:\n{result}"
    except Exception as e:
        prompt = f"Tool {selected_tool} failed:\n{e}"