import requests
from core.env_fetcher import EnvFetcher


class InstructLabProvider:
    def __init__(self):
        self.url = EnvFetcher.get("AI_URL")
        self.model = EnvFetcher.get("AI_MODEL")

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
