def handle(ai_provider, prompt, text):
    try:
        return ai_provider.improve_text(prompt, text)
    except Exception as e:
        print(f"⚠️ AI cleanup failed: {e}")
        return text
