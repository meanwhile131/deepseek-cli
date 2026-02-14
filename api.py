from pow_solve import POWSolver
import requests
import json

COMPLETION_PATH = "/api/v0/chat/completion"
POW_REQUEST = json.dumps({"target_path": COMPLETION_PATH})


class DeepSeekAPI:
    def __init__(self, token: str, pow_solver: POWSolver):
        self.session = requests.Session()
        self.session.headers["authorization"] = f"Bearer {token}"
        self.session.headers["Content-Type"] = "application/json"
        self.pow_solver = pow_solver

    def create_chat(self):
        r = self.session.post(
            "https://chat.deepseek.com/api/v0/chat_session/create", "{}")
        chat = r.json()["data"]["biz_data"]
        return chat

    def complete(self, chat_id: str, prompt: str) -> str:
        r = self.session.post(
            "https://chat.deepseek.com/api/v0/chat/create_pow_challenge", POW_REQUEST)
        challenge = r.json()["data"]["biz_data"]["challenge"]
        self.session.headers["x-ds-pow-response"] = self.pow_solver.solve_challenge(challenge)

        request = {
            "chat_session_id": chat_id,
            "prompt": prompt,
            "ref_file_ids": []
        }
        r = self.session.post(
            f"https://chat.deepseek.com{COMPLETION_PATH}", json.dumps(request), stream=True)
        out = ""
        for line in r.iter_lines():
            if line == b"event: finish":
                break
            if not line.startswith(b"data: "):
                continue
            data: dict = json.loads(line[6:])
            if data.get("v") is None:
                continue
            if (data.get("p") == "response/content" or data.get("p") is None) and isinstance(data["v"], str):
                out += data["v"]
        return out