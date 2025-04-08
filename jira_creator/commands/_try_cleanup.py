from exceptions.exceptions import AiError


def _try_cleanup(ai_provider, prompt, text):
    try:
        return ai_provider.improve_text(prompt, text)
    except AiError as e:
        msg = f"⚠️ AI cleanup failed: {e}"
        print(msg)
        raise (AiError(msg))
