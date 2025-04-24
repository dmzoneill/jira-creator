"""
This module provides a class GPT4AllProvider that serves as a wrapper for the GPT4All model.
It allows improving text by generating an improved version based on the given prompt and text.
The GPT4AllProvider class has an __init__ method to initialize the model and an improve_text method to generate
improved text.
"""

from exceptions.exceptions import GTP4AllError
from gpt4all import GPT4All


class GPT4AllProvider:
    """
    This class provides a wrapper to interact with the GPT4All model for text improvement.

    Attributes:
    - model_name (str): The name of the GPT4All model to be used, defaults to "ggml-gpt4all-j-v1.3-groovy".
    - model: An instance of the GPT4All model initialized with the specified model_name.

    Methods:
    - improve_text(prompt: str, text: str) -> str: Takes a prompt and text as input, generates an instruction combining
    them, uses the GPT4All model to improve the text, and returns the improved version.
    """

    def __init__(self, model_name: str = "ggml-gpt4all-j-v1.3-groovy"):
        """
        Initialize a new instance of the GPT4AllModel class with the specified model name.

        Arguments:
        - model_name (str): The name of the GPT4All model to be used. Defaults to "ggml-gpt4all-j-v1.3-groovy".

        Exceptions:
        - GTP4AllError: Raised if there is an error loading the GPT4All model.

        Side Effects:
        - Initializes the model attribute with an instance of the GPT4All class using the provided model name.
        """

        self.model_name = model_name
        try:
            self.model = GPT4All(model_name)
        except GTP4AllError as e:
            raise GTP4AllError(e) from e

    def improve_text(self, prompt: str, text: str) -> str:
        """
        Improve the given text by generating an improved version based on the provided prompt.

        Arguments:
        - prompt (str): The prompt to be displayed before the text for improvement.
        - text (str): The original text that needs to be improved.

        Return:
        - str: The improved version of the text, maintaining the original structure.

        Side Effects:
        - Calls a model to generate the improved text based on the prompt and original text.
        """

        instruction = (
            f"{prompt}\n\n"
            f"---\n"
            f"{text}\n"
            f"---\n\n"
            f"Please provide the improved version of the text, maintaining the structure."
        )
        response = self.model.generate(instruction, max_tokens=1024, temp=0.3)
        return response.strip()
