from exceptions.exceptions import GTP4AllError
from gpt4all import GPT4All


class GPT4AllProvider:
    def __init__(self, model_name: str = "ggml-gpt4all-j-v1.3-groovy"):
        self.model_name = model_name
        try:
            self.model = GPT4All(model_name)
        except GTP4AllError as e:
            raise GTP4AllError(RuntimeError(f"Failed to load GPT4All model: {e}"))

    def improve_text(self, prompt: str, text: str) -> str:
        instruction = (
            f"{prompt}\n\n"
            f"---\n"
            f"{text}\n"
            f"---\n\n"
            f"Please provide the improved version of the text, maintaining the structure."
        )
        response = self.model.generate(instruction, max_tokens=1024, temp=0.3)
        return response.strip()
