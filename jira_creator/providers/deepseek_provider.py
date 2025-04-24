"""
This module provides a DeepSeekProvider class for interacting with an AI service to improve text quality.
The DeepSeekProvider class initializes with default endpoint values fetched from environment variables.
It includes a method improve_text(prompt, text) to send a POST request to the AI service and improve the given text.
If successful, it returns the improved text; otherwise, it raises an AiError with details of the failure.
"""

import json

import requests
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import AiError


class DeepSeekProvider:
    """
    A class that provides methods to interact with a DeepSeek AI service.

    Attributes:
    - url (str): The endpoint URL for the AI service, defaults to a local or proxied endpoint.
    - headers (dict): The headers for the HTTP request, with the Content-Type set to application/json.
    - model (str): The AI model used for processing the text data.
    """

    def __init__(self):
        """
        Initialize the AIEndpoint class with default values for URL, headers, and model.

        Arguments:
        - self: The instance of the class.

        Side Effects:
        - Initializes the URL, headers, and model attributes using environment variables fetched by EnvFetcher.
        """

        # Defaults to a local or proxied endpoint; override with env var
        self.url = EnvFetcher.get("AI_URL")
        self.headers = {"Content-Type": "application/json"}
        self.model = EnvFetcher.get("AI_MODEL")

    def improve_text(self, prompt: str, text: str) -> str:
        """
        Concatenates a given prompt with a text, separated by two new lines.

        Arguments:
        - prompt (str): The initial prompt to be displayed.
        - text (str): The text to be appended to the prompt.

        Return:
        - str: The combined prompt and text.

        """

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
            raise AiError(
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
        except json.JSONDecodeError as e:
            raise AiError(e) from e
