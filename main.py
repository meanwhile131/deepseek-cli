import os
from pow_solve import POWSolver
from api import DeepSeekAPI

token = os.getenv('TOKEN', None)
if token is None:
    print("no TOKEN env var found")
    exit(1)

pow_solver = POWSolver("sha3_wasm_bg.7b9ca65ddd.wasm")
api = DeepSeekAPI(token, pow_solver)
chat = api.create_chat()
message = {}
while True:
    try:
        prompt = input("> ")
    except EOFError:
        break
    message = api.complete(chat["id"], prompt, parent_message_id=message.get("message_id"), thinking=True, search=True)
    print("\033[1mReasoning:\033[0m")
    print(message["thinking_content"])
    print("\033[1mOutput:\033[0m")
    print(message["content"])