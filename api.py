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

    def _set_pow_header(self):
        r = self.session.post(
            "https://chat.deepseek.com/api/v0/chat/create_pow_challenge", POW_REQUEST)
        challenge = r.json()["data"]["biz_data"]["challenge"]
        self.session.headers["x-ds-pow-response"] = self.pow_solver.solve_challenge(
            challenge)

    def complete(self, chat_id: str, prompt: str, parent_message_id: int = None) -> str:
        self._set_pow_header()
        request = {
            "chat_session_id": chat_id,
            "prompt": prompt,
            "parent_message_id": parent_message_id,
            "ref_file_ids": []
        }
        r = self.session.post(
            f"https://chat.deepseek.com{COMPLETION_PATH}", json.dumps(request), stream=True)
        message = {}
        for line in r.iter_lines():
            if line == b"event: finish":
                break
            if not line.startswith(b"data: "):
                continue
            data: dict = json.loads(line[6:])

            v = data.get("v")
            if v is None:
                continue
            if isinstance(v, dict):  # received the initial response
                message = v
                continue

            path: str = data.get("p")
            if path is None:
                message["response"]["content"] += v
                continue
            self._set_property_by_path(message, path, v)

        return message["response"]

    def _set_property_by_path(self, obj: dict, path: str, value):
        keys = path.split("/")
        data = obj.copy()
        for key in keys[:-1]:
            if not isinstance(data.get(key), dict):
                return False
            data = data[key]
        last_key = keys[-1]
        data[last_key] = value
        return True
