class NoAIProvider:
    """
    A class representing a provider for improving text using AI.

    Attributes:
    - prompt (str): A string representing the prompt for text improvement.
    - text (str): A string representing the text to be improved.
    """

    def improve_text(self, prompt: str, text: str) -> str:
        """
        Summary:
        This function returns the original text as is, indicating that no AI provider is configured or available to
        improve the text.

        Arguments:
        - prompt (str): The prompt or message indicating the lack of AI provider.
        - text (str): The original text that is returned as there is no AI provider available.

        Return:
        - str: The original text passed as an argument.

        """

        print("⚠️  No AI provider configured or available. Returning original text.")
        return text
