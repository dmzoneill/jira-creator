#!/usr/bin/env python
"""Unit tests for VertexAIProvider Claude and Gemini routing."""

import builtins
import importlib
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from jira_creator.exceptions.exceptions import AiError
from jira_creator.providers.vertex_provider import VertexAIProvider

CLAUDE_MODEL = "claude-3-5-sonnet@20241022"
GEMINI_MODEL = "gemini-1.5-pro"
LOCATION = "us-central1"
ENV_GET = "jira_creator.providers.vertex_provider.EnvFetcher.get"


def claude_env(project: str = "test-project", **extra: str) -> dict[str, str]:
    """Environment map for a Claude-on-Vertex provider."""
    values = {
        "JIRA_AI_MODEL": CLAUDE_MODEL,
        "GOOGLE_CLOUD_LOCATION": LOCATION,
        "ANTHROPIC_VERTEX_PROJECT_ID": project,
    }
    values.update(extra)
    return values


def gemini_env(project: str = "test-project", **extra: str) -> dict[str, str]:
    """Environment map for a Gemini-on-Vertex provider."""
    values = {
        "JIRA_AI_MODEL": GEMINI_MODEL,
        "GOOGLE_CLOUD_LOCATION": LOCATION,
        "GOOGLE_CLOUD_PROJECT": project,
    }
    values.update(extra)
    return values


@contextmanager
def patched_env(env: dict[str, str], missing_key: str | None = None) -> Iterator[None]:
    """Patch EnvFetcher.get for the duration of a provider call."""

    def env_get(key: str, default: Any = None) -> Any:
        if missing_key and key == missing_key:
            return env_get("GOOGLE_CLOUD_PROJECT", default)
        return env.get(key, default)

    with patch(ENV_GET) as mock_env:
        mock_env.side_effect = env_get
        yield


@contextmanager
def built(env: dict[str, str], missing_key: str | None = None) -> Iterator[VertexAIProvider]:
    """Construct a provider while EnvFetcher is patched."""
    with patched_env(env, missing_key):
        yield VertexAIProvider()


@contextmanager
def claude_modules(text: str | None = None, empty: bool = False, error: str | None = None) -> Iterator[tuple]:
    """Install a fake anthropic module that returns one Claude message."""
    module = MagicMock()
    client = MagicMock()
    if error:
        client.messages.create.side_effect = Exception(error)
    else:
        message = MagicMock()
        if empty:
            message.content = []
        else:
            block = MagicMock()
            block.text = text
            message.content = [block]
        client.messages.create.return_value = message
    module.AnthropicVertex.return_value = client
    with patch.dict(sys.modules, {"anthropic": module}):
        yield module, client


@contextmanager
def gemini_modules(text: str | None = None, empty: bool = False, error: str | None = None) -> Iterator[tuple]:
    """Install fake vertexai modules that return one Gemini response."""
    vertexai = MagicMock()
    generative_models = MagicMock()
    model = MagicMock()
    if error:
        model.generate_content.side_effect = Exception(error)
    else:
        response = MagicMock()
        response.text = None if empty else text
        model.generate_content.return_value = response
    generative_models.GenerativeModel.return_value = model
    vertexai.generative_models = generative_models
    modules = {"vertexai": vertexai, "vertexai.generative_models": generative_models}
    with patch.dict(sys.modules, modules):
        yield vertexai, generative_models, model


@contextmanager
def block_imports(predicate: Callable[[str], bool]) -> Iterator[None]:
    """Raise ImportError for module names selected by predicate."""
    original_import = builtins.__import__

    def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if predicate(name):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        yield


def test_block_imports_still_loads_unrelated_modules():
    """Import blocking leaves modules outside the predicate alone."""
    with block_imports(lambda name: name == "anthropic"):
        module = importlib.import_module("pathlib")
    assert module.Path(".") is not None


def assert_import_error(
    env: dict[str, str], predicate: Callable[[str], bool], method: str, args: tuple, expected: str
) -> None:
    """Provider methods report a missing SDK with the install hint."""
    with built(env) as provider, block_imports(predicate), pytest.raises(AiError) as exc_info:
        getattr(provider, method)(*args)
    assert expected in str(exc_info.value)


def claude_failure(method: str, args: tuple, empty: bool = False, error: str | None = None) -> str:
    """Return the AiError message from a failing Claude call."""
    with built(claude_env()) as provider, claude_modules(empty=empty, error=error), pytest.raises(AiError) as exc_info:
        getattr(provider, method)(*args)
    return str(exc_info.value)


def gemini_failure(method: str, args: tuple, empty: bool = False, error: str | None = None) -> str:
    """Return the AiError message from a failing Gemini call."""
    with built(gemini_env()) as provider, gemini_modules(empty=empty, error=error), pytest.raises(AiError) as exc_info:
        getattr(provider, method)(*args)
    return str(exc_info.value)


def claude_text(method: str, args: tuple, text: str) -> str:
    """Return the text from a successful Claude call."""
    with built(claude_env()) as provider, claude_modules(text=text):
        return getattr(provider, method)(*args)


def gemini_text(method: str, args: tuple, text: str) -> str:
    """Return the text from a successful Gemini call."""
    with built(gemini_env()) as provider, gemini_modules(text=text):
        return getattr(provider, method)(*args)


def test_vertex_provider_detects_claude_model():
    """Claude model names select the Anthropic project and location."""
    env = claude_env(project="my-claude-project", GOOGLE_CLOUD_PROJECT="my-general-project")
    with built(env) as provider:
        assert provider.model_type == "claude"
        assert provider.model == CLAUDE_MODEL
        assert provider.project_id == "my-claude-project"
        assert provider.location == LOCATION


def test_vertex_provider_detects_gemini_model():
    """Gemini model names select the Google Cloud project."""
    with built(gemini_env(project="my-gemini-project")) as provider:
        assert provider.model_type == "gemini"
        assert provider.model == GEMINI_MODEL
        assert provider.project_id == "my-gemini-project"
        assert provider.location == LOCATION


def test_vertex_provider_rejects_invalid_model():
    """Model names outside claude- and gemini- are rejected at init."""
    env = {"JIRA_AI_MODEL": "gpt-4", "GOOGLE_CLOUD_LOCATION": LOCATION, "GOOGLE_CLOUD_PROJECT": "my-project"}
    with patched_env(env), pytest.raises(AiError) as exc_info:
        VertexAIProvider()
    message = str(exc_info.value)
    assert "Unsupported Vertex AI model" in message
    assert "gpt-4" in message


def test_vertex_provider_claude_improve_text():
    """improve_text returns Claude text and passes region plus project."""
    with built(claude_env()) as provider, claude_modules(text="Improved text from Claude") as (module, client):
        result = provider.improve_text("test prompt", "test input")
    assert result == "Improved text from Claude"
    module.AnthropicVertex.assert_called_once_with(region=LOCATION, project_id="test-project")
    client.messages.create.assert_called_once()


def test_vertex_provider_gemini_improve_text():
    """improve_text initializes Gemini and returns the generated text."""
    with built(gemini_env()) as provider, gemini_modules(text="Improved text from Gemini") as (vertexai, models, model):
        result = provider.improve_text("test prompt", "test input")
    assert result == "Improved text from Gemini"
    vertexai.init.assert_called_once_with(project="test-project", location=LOCATION)
    models.GenerativeModel.assert_called_once_with(GEMINI_MODEL)
    model.generate_content.assert_called_once()


def test_vertex_provider_claude_api_failure():
    """Claude SDK exceptions become an AiError."""
    message = claude_failure("improve_text", ("test prompt", "test input"), error="API Error")
    assert "Claude Vertex AI call failed" in message


def test_vertex_provider_gemini_api_failure():
    """Gemini SDK exceptions become an AiError."""
    message = gemini_failure("improve_text", ("test prompt", "test input"), error="API Error")
    assert "Gemini Vertex AI call failed" in message


def test_vertex_provider_claude_missing_dependency():
    """A missing anthropic package names the extra to install."""
    assert_import_error(
        claude_env(),
        lambda name: name == "anthropic",
        "improve_text",
        ("test prompt", "test input"),
        "anthropic[vertex] package not installed",
    )


def test_vertex_provider_gemini_missing_dependency():
    """A missing vertexai package names google-cloud-aiplatform."""
    assert_import_error(
        gemini_env(),
        lambda name: "vertexai" in name,
        "improve_text",
        ("test prompt", "test input"),
        "google-cloud-aiplatform package not installed",
    )


def test_vertex_provider_uses_anthropic_project_id():
    """Claude prefers ANTHROPIC_VERTEX_PROJECT_ID over the general project."""
    env = claude_env(project="claude-specific-project", GOOGLE_CLOUD_PROJECT="general-project")
    with built(env) as provider:
        assert provider.project_id == "claude-specific-project"


def test_vertex_provider_claude_fallback_to_gcp_project():
    """Claude falls back to GOOGLE_CLOUD_PROJECT when the Anthropic project is unset."""
    env = {
        "JIRA_AI_MODEL": CLAUDE_MODEL,
        "GOOGLE_CLOUD_LOCATION": LOCATION,
        "GOOGLE_CLOUD_PROJECT": "general-project",
    }
    with built(env, missing_key="ANTHROPIC_VERTEX_PROJECT_ID") as provider:
        assert provider.project_id == "general-project"


def test_vertex_provider_claude_analyze_error():
    """analyze_error returns the Claude analysis text."""
    assert claude_text("analyze_error", ("test prompt", '{"error": "test"}'), "Error analysis result") == (
        "Error analysis result"
    )


def test_vertex_provider_gemini_analyze_error():
    """analyze_error returns the Gemini analysis text."""
    assert gemini_text("analyze_error", ("test prompt", '{"error": "test"}'), "Gemini error analysis") == (
        "Gemini error analysis"
    )


def test_vertex_provider_claude_analyze_and_fix_error():
    """analyze_and_fix_error keeps the Claude JSON payload."""
    result = claude_text(
        "analyze_and_fix_error",
        ("test prompt", '{"error": "test"}'),
        '{"fix_type": "codebase", "confidence": 0.9}',
    )
    assert '{"fix_type": "codebase"' in result


def test_vertex_provider_gemini_analyze_and_fix_error():
    """analyze_and_fix_error keeps the Gemini JSON payload."""
    result = gemini_text(
        "analyze_and_fix_error",
        ("test prompt", '{"error": "test"}'),
        '{"fix_type": "payload", "confidence": 0.8}',
    )
    assert '{"fix_type": "payload"' in result


def test_vertex_provider_claude_analyze_error_empty_response():
    """An empty Claude analysis is reported as an empty response."""
    assert "Empty response" in claude_failure("analyze_error", ("test prompt", '{"error": "test"}'), empty=True)


def test_vertex_provider_claude_analyze_error_api_failure():
    """Claude analysis failures name the Claude backend."""
    message = claude_failure("analyze_error", ("test prompt", '{"error": "test"}'), error="API Error")
    assert "Claude Vertex AI call failed" in message


def test_vertex_provider_gemini_analyze_error_empty_response():
    """An empty Gemini analysis is reported as an empty response."""
    assert "Empty response" in gemini_failure("analyze_error", ("test prompt", '{"error": "test"}'), empty=True)


def test_vertex_provider_gemini_analyze_error_api_failure():
    """Gemini analysis failures name the Gemini backend."""
    message = gemini_failure("analyze_error", ("test prompt", '{"error": "test"}'), error="API Error")
    assert "Gemini Vertex AI call failed" in message


def test_vertex_provider_claude_analyze_and_fix_error_empty_response():
    """An empty Claude fix proposal is reported as an empty response."""
    message = claude_failure("analyze_and_fix_error", ("test prompt", '{"error": "test"}'), empty=True)
    assert "Empty response" in message


def test_vertex_provider_claude_analyze_and_fix_error_api_failure():
    """Claude fix-proposal failures name the Claude backend."""
    message = claude_failure("analyze_and_fix_error", ("test prompt", '{"error": "test"}'), error="API Error")
    assert "Claude Vertex AI call failed" in message


def test_vertex_provider_gemini_analyze_and_fix_error_empty_response():
    """An empty Gemini fix proposal is reported as an empty response."""
    message = gemini_failure("analyze_and_fix_error", ("test prompt", '{"error": "test"}'), empty=True)
    assert "Empty response" in message


def test_vertex_provider_gemini_analyze_and_fix_error_api_failure():
    """Gemini fix-proposal failures name the Gemini backend."""
    message = gemini_failure("analyze_and_fix_error", ("test prompt", '{"error": "test"}'), error="API Error")
    assert "Gemini Vertex AI call failed" in message


def test_vertex_provider_claude_improve_text_empty_response():
    """An empty Claude improvement is reported as an empty response."""
    assert "Empty response" in claude_failure("improve_text", ("test prompt", "test input"), empty=True)


def test_vertex_provider_gemini_improve_text_empty_response():
    """An empty Gemini improvement is reported as an empty response."""
    assert "Empty response" in gemini_failure("improve_text", ("test prompt", "test input"), empty=True)


def _unknown_model_message(method: str, args: tuple) -> str:
    with built(claude_env()) as provider:
        provider.model_type = "unknown"
        with pytest.raises(AiError) as exc_info:
            getattr(provider, method)(*args)
    return str(exc_info.value)


def test_vertex_provider_unknown_model_type_improve_text():
    """improve_text rejects a model type overwritten after init."""
    assert "Unknown model type: unknown" in _unknown_model_message("improve_text", ("test prompt", "test input"))


def test_vertex_provider_unknown_model_type_analyze_error():
    """analyze_error rejects a model type overwritten after init."""
    message = _unknown_model_message("analyze_error", ("test prompt", '{"error": "test"}'))
    assert "Unknown model type: unknown" in message


def test_vertex_provider_unknown_model_type_analyze_and_fix_error():
    """analyze_and_fix_error rejects a model type overwritten after init."""
    message = _unknown_model_message("analyze_and_fix_error", ("test prompt", '{"error": "test"}'))
    assert "Unknown model type: unknown" in message


def test_vertex_provider_claude_analyze_error_missing_dependency():
    """analyze_error reports a missing anthropic package."""
    assert_import_error(
        claude_env(),
        lambda name: name == "anthropic",
        "analyze_error",
        ("test prompt", '{"error": "test"}'),
        "anthropic[vertex] package not installed",
    )


def test_vertex_provider_gemini_analyze_error_missing_dependency():
    """analyze_error reports a missing vertexai package."""
    assert_import_error(
        gemini_env(),
        lambda name: "vertexai" in name,
        "analyze_error",
        ("test prompt", '{"error": "test"}'),
        "google-cloud-aiplatform package not installed",
    )


def test_vertex_provider_claude_analyze_and_fix_error_missing_dependency():
    """analyze_and_fix_error reports a missing anthropic package."""
    assert_import_error(
        claude_env(),
        lambda name: name == "anthropic",
        "analyze_and_fix_error",
        ("test prompt", '{"error": "test"}'),
        "anthropic[vertex] package not installed",
    )


def test_vertex_provider_gemini_analyze_and_fix_error_missing_dependency():
    """analyze_and_fix_error reports a missing vertexai package."""
    assert_import_error(
        gemini_env(),
        lambda name: "vertexai" in name,
        "analyze_and_fix_error",
        ("test prompt", '{"error": "test"}'),
        "google-cloud-aiplatform package not installed",
    )
