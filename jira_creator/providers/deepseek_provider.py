import json

import requests
from core.env_fetcher import EnvFetcher


class DeepSeekProvider:
    def __init__(self):
        # Defaults to a local or proxied endpoint; override with env var
        self.url = EnvFetcher.get("AI_URL")
        self.headers = {"Content-Type": "application/json"}
        self.model = EnvFetcher.get("AI_MODEL")

    def improve_text(self, prompt: str, text: str) -> str:
        full_prompt = f"{prompt}\n\n{text}"

        # Send the POST request
        response = requests.post(
            self.url,
            headers=self.headers,
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
            },  # Change to non-streaming
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(
                f"DeepSeek request failed: {response.status_code} - {response.text}"
            )

        # Parse the entire response at once
        try:
            response_data = response.json()
            entire_response = response_data.get("response", "").strip()
            # Replace <think> with HTML tags if needed
            entire_response = entire_response.replace("<think>", "")
            entire_response = entire_response.replace("</think>", "")
            return entire_response
        except json.JSONDecodeError:
            raise Exception(f"Failed to parse response: {response.text}")
