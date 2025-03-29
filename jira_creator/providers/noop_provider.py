class NoAIProvider:
    def improve_text(self, prompt: str, text: str) -> str:
        print("⚠️  No AI provider configured or available. Returning original text.")
        return text
