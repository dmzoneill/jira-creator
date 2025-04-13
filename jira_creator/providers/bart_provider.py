import requests
from core.env_fetcher import EnvFetcher


class BARTProvider:
    def __init__(self):
        # Default to local endpoint or override with env var
        self.url = EnvFetcher.get("AI_URL")
        self.headers = {"Content-Type": "application/json"}

    def improve_text(self, prompt: str, text: str) -> str:
        full_prompt = f"{prompt}\n\n{text}"
        response = requests.post(
            self.url, headers=self.headers, json={"text": full_prompt}, timeout=30
        )
        if response.status_code == 200:
            return response.json().get("output", "").strip()

        raise Exception(
            f"BART request failed: {response.status_code} - {response.text}"
        )
