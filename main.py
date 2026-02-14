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
You are an AI assistant inside a CLI application. You are able to invoke tools, but do so only if needed. To invoke a tool, output ONLY it's exact name, a newline, and it's arguments. You may only make one tool call per message. There must be no output after or before this. Available tools:
"""
for tool in tools:
    system_prompt += f"{tool}: {tools[tool]["description"]}\n"
system_prompt += """
User prompt:
"""
first_prompt = True
prompt = None
while True:
    if prompt == None:
        try:
            prompt = input("\033[1m>\033[0m ")
        except EOFError:
            break
    if first_prompt:
        prompt = system_prompt + prompt
        first_prompt = False
    message = api.complete(chat["id"], prompt, parent_message_id=message.get(
        "message_id"), thinking=True, search=True)
    content = message["content"]

    selected_tool = None
    try:
        first_newline_idx = content.index('\n')
        tool = content[:first_newline_idx]
        if tool in tools:
            selected_tool = tool
    except ValueError:
        pass

    print("\033[1mReasoning:\033[0m")
    print(message["thinking_content"])
    if selected_tool == None:
        print("\033[1mOutput:\033[0m")
        print(content)
        prompt = None  # ask the user for their new prompt
        continue
    print(f"\033[1mCalling tool {selected_tool}\033[0m")
    try:
        args = content[first_newline_idx+1:]
        result = tools[selected_tool]["function"](args)
        prompt = f"Tool {selected_tool} returned:\n{result}"
    except Exception as e:
        prompt = f"Tool {selected_tool} failed:\n{e}"
