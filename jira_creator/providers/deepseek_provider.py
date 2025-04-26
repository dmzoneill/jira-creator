#!/usr/bin/env python
"""
This module provides the DeepSeekProvider class for interacting with a DeepSeek AI service to enhance text quality.

The DeepSeekProvider class is initialized with default endpoint values retrieved from environment variables. It
includes the method improve_text(prompt, text) which sends a POST request to the AI service to improve the provided
text. Upon success, it returns the enhanced text; if it fails, an AiError is raised with details of the failure.

Classes:
- DeepSeekProvider: A class for managing interactions with the DeepSeek AI service.

Attributes of DeepSeekProvider:
- url (str): The endpoint URL for the AI service, defaults to a local or proxied endpoint.
- headers (dict[str, str]): The headers for the HTTP request, with Content-Type set to application/json.
- model (str): The AI model used for processing the text data.

Methods:
- improve_text(prompt: str, text: str) -> str:
Concatenates a given prompt with text, sends a request to the AI service, and returns the improved text.

Exceptions:
- AiError: Raised when the POST request fails or if there is an issue with the JSON response.
"""

# pylint: disable=too-few-public-methods

import json
from typing import Dict

import requests
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import AiError
from providers.ai_provider import AIProvider


class DeepSeekProvider(AIProvider):
    """
    A class that provides methods to interact with a DeepSeek AI service.

    Attributes:
    - url (str): The endpoint URL for the AI service, defaults to a local or proxied endpoint.
    - headers (Dict[str, str]): The headers for the HTTP request, with the Content-Type set to application/json.
    - model (str): The AI model used for processing the text data.
    """

    def __init__(self) -> None:
        """
        Initialize the AIEndpoint class with default values for URL, headers, and model.

        Arguments:
        - self: The instance of the class.

        Side Effects:
        - Initializes the URL, headers, and model attributes using environment variables fetched by EnvFetcher.
        """

        self.url: str = EnvFetcher.get("AI_URL")
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        self.model: str = EnvFetcher.get("AI_MODEL")

    def improve_text(self, prompt: str, text: str) -> str:
        """
        Concatenates a given prompt with a text, separated by two new lines.

        Arguments:
        - prompt (str): The initial prompt to be displayed.
        - text (str): The text to be appended to the prompt.

        Return:
        - str: The combined prompt and text.

        Exceptions:
        - AiError: Raised if the POST request fails or if there is an issue parsing the JSON response.

        Side Effects:
        - Sends a POST request using the provided URL, headers, model, and timeout settings.
        - Modifies the response by removing specific HTML tags ("<think>") if present.
        """

        full_prompt: str = f"{prompt}\n\n{text}"

        # Send the POST request
        response: requests.Response = requests.post(
            self.url,
            headers=self.headers,
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise AiError(
                f"DeepSeek request failed: {response.status_code} - {response.text}"
            )

        # Parse the entire response at once
        try:
            response_data: Dict[str, str] = response.json()
            entire_response: str = response_data.get("response", "").strip()
            entire_response = entire_response.replace("<think>", "").replace(
                "</think>", ""
            )
            return entire_response
        except json.JSONDecodeError as e:
            raise AiError(e) from e
