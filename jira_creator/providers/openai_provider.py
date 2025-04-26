#!/usr/bin/env python
"""
This module provides a class, OpenAIProvider, for interacting with the OpenAI API to improve text based on a given
prompt and text. It includes a method, improve_text, that sends a request to the OpenAI API and returns the improved
text. The class initializes with API key, endpoint, and model fetched from environment variables using the EnvFetcher
class. It also handles exceptions by raising AiError in case of API call failure.

Class OpenAIProvider:
This class provides a wrapper to interact with the OpenAI API for text completion and improvement.

Attributes:
- api_key (str): The API key used to authenticate requests to the OpenAI API.
- endpoint (str): The URL endpoint for making requests to the OpenAI API chat completions.
- model (str): The model identifier used for text completion and improvement.

Methods:
- improve_text(prompt: str, text: str) -> str: Sends a request to the OpenAI API to improve the given text based on
a prompt. It returns the improved text after processing. Raises an AiError if the API call fails.
"""

# pylint: disable=too-few-public-methods

import requests
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import AiError
from providers.AiProvider import AiProvider


class OpenAIProvider(AiProvider):
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

    def __init__(self):
        """
        Initialize a Chatbot instance with API key, endpoint, and model information.

        Arguments:
        - self: The Chatbot instance itself.

        Side Effects:
        - Sets the API key, endpoint URL, and model information for the Chatbot instance.
        """

        self.api_key = EnvFetcher.get("AI_API_KEY")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.model = EnvFetcher.get("AI_MODEL")

    # /* jscpd:ignore-start */
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
        """

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

        response = requests.post(self.endpoint, json=body, headers=headers, timeout=120)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        raise AiError(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )

    # /* jscpd:ignore-end */
