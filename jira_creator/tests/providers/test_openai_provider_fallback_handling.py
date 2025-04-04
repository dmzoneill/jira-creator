import requests
from providers.openai_provider import OpenAIProvider


def test_openai_response_handling():
    mock = type(
        "Response",
        (),
        {
            "status_code": 200,
            "json": lambda self: {"choices": [{"message": {"content": "✓"}}]},
        },
    )
    requests.post = lambda *a, **kw: mock()
    provider = OpenAIProvider()
    result = provider.improve_text("prompt", "dirty text")
    assert result == "✓"
