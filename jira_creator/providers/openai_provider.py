import os

import requests


class OpenAIProvider:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("AI_API_KEY not set in environment.")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")

    def improve_text(self, prompt: str, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.8,
        }

        response = requests.post(self.endpoint, json=body, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        raise Exception(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )
