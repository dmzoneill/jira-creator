import os

import requests


class InstructLabProvider:
    def __init__(self):
        self.url = os.getenv("INSTRUCTLAB_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("INSTRUCTLAB_MODEL", "instructlab")

    def improve_text(self, prompt: str, text: str) -> str:
        full_prompt = f"{prompt}\n\n{text}"
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.3},
            },
            timeout=60,
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        raise Exception(
            f"InstructLab request failed: {response.status_code} - {response.text}"
        )
