import requests
import os
import json
from pow_solve import POWSolver
from api import DeepSeekAPI

token = os.getenv('TOKEN', None)
if token is None:
    print("no TOKEN env var found")
    exit(1)

pow_solver = POWSolver("sha3_wasm_bg.7b9ca65ddd.wasm")
api = DeepSeekAPI(token, pow_solver)
chat = api.create_chat()
print(api.complete(chat["id"], "hi"))