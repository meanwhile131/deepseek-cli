import requests
import os
import json
from pow_solve import POWSolver

COMPLETION_PATH = "/api/v0/chat/completion"
POW_REQUEST = json.dumps({"target_path": COMPLETION_PATH})

token = os.getenv('TOKEN', None)
if token is None:
    print("no TOKEN env var found")
    exit(1)

pow_solver = POWSolver("sha3_wasm_bg.7b9ca65ddd.wasm")
s = requests.Session()
s.headers["authorization"] = f"Bearer {token}"
s.headers["Content-Type"] = "application/json"
r = s.post("https://chat.deepseek.com/api/v0/chat_session/create", "{}")
chat = r.json()["data"]["biz_data"]

r = s.post(
    "https://chat.deepseek.com/api/v0/chat/create_pow_challenge", POW_REQUEST)
challenge = r.json()["data"]["biz_data"]["challenge"]
result = pow_solver.solve_challenge(challenge)
s.headers["x-ds-pow-response"] = result

request = {
    "chat_session_id": chat["id"],
    "prompt": "hi",
    "ref_file_ids": []
}
r = s.post(f"https://chat.deepseek.com{COMPLETION_PATH}", json.dumps(request))
print(r.text)
