from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Abstract base class that defines the required interface for all AI providers.
    """

    @abstractmethod
    def improve_text(self, prompt: str, text: str) -> str:
        """
        This method should be implemented by each AI provider to improve the text based on the prompt.

        Arguments:
        - prompt (str): The initial prompt to provide context for improving the text.
        - text (str): The text to be improved.

        Returns:
        - str: The improved version of the text.
        """
