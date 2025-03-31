import os

import requests


class DeepSeekProvider:
    def __init__(self):
        # Defaults to a local or proxied endpoint; override with env var
        self.url = os.getenv("DEEPSEEK_URL", "http://localhost:8000/deepseek")
        self.headers = {"Content-Type": "application/json"}

    def improve_text(self, prompt: str, text: str) -> str:
        full_prompt = f"{prompt}\n\n{text}"
        response = requests.post(
            self.url, headers=self.headers, json={"text": full_prompt}, timeout=30
        )
        if response.status_code == 200:
            return response.json().get("output", "").strip()

        raise Exception(
            f"DeepSeek request failed: {response.status_code} - {response.text}"
        )
