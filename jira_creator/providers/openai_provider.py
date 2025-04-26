#!/usr/bin/env python
"""
This module provides the OpenAIProvider class, which serves as a wrapper for interacting with the OpenAI API to enhance
text based on specified prompts. The primary functionality is encapsulated in the improve_text method, which sends a
request to the OpenAI API and returns the improved text. The class also handles the retrieval of the API key, endpoint,
and model from environment variables using the EnvFetcher class, and it raises an AiError in case of any API call
failures.

Classes:
- OpenAIProvider: A class designed to facilitate text completion and improvement through the OpenAI API.

Attributes:
- api_key (str): The API key for authenticating requests to the OpenAI API.
- endpoint (str): The endpoint URL for making requests to the OpenAI API chat completions.
- model (str): The identifier for the model utilized in text completion and improvement.

Methods:
- improve_text(prompt: str, text: str) -> str: Accepts a prompt and text, requests the OpenAI API to enhance the text,
and returns the improved version. Raises an AiError if the API call is unsuccessful.
"""

# pylint: disable=too-few-public-methods

import requests
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import AiError
from providers.ai_provider import AIProvider


class OpenAIProvider(AIProvider):
    """
    This class provides a wrapper to interact with the OpenAI API for text completion and improvement.

    Attributes:
    - api_key (str): The API key used to authenticate requests to the OpenAI API.
    - endpoint (str): The URL endpoint for making requests to the OpenAI API chat completions.
    - model (str): The model identifier used for text completion and improvement.

    Methods:
    - improve_text(prompt: str, text: str) -> str: Sends a request to the OpenAI API to improve the given text based on
    a prompt. It returns the improved text after processing. Raises an AiError if the API call fails.
    """

    def __init__(self) -> None:
        """
        Initialize a Chatbot instance with API key, endpoint, and model information.

        Arguments:
        - self: The Chatbot instance itself.

        Side Effects:
        - Sets the API key attribute using the value fetched from the environment variable "AI_API_KEY".
        - Sets the endpoint attribute to "https://api.openai.com/v1/chat/completions".
        - Sets the model attribute using the value fetched from the environment variable "AI_MODEL".
        """
        self.api_key: str = EnvFetcher.get("AI_API_KEY")
        self.endpoint: str = "https://api.openai.com/v1/chat/completions"
        self.model: str = EnvFetcher.get("AI_MODEL")

    def improve_text(self, prompt: str, text: str) -> str:
        """
        Improves the given text using an external API.

        Arguments:
        - prompt (str): The prompt to provide context for improving the text.
        - text (str): The text to be improved.

        Return:
        - str: The improved text after processing with the external API.

        Side Effects:
        - Makes a request to an external API using the provided prompt and text.

        Exceptions:
        - AiError: Raised when the OpenAI API call fails, providing the status code and response text.
        """
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.8,
        }

        response: requests.Response = requests.post(
            self.endpoint, json=body, headers=headers, timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        raise AiError(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )
