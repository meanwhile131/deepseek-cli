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
msg = api.complete(chat["id"], "hi")
print(msg["content"])
msg = api.complete(chat["id"], "what is the longest bridge in the world", parent_message_id=msg["message_id"], thinking=True, search=True)
print(msg["content"])