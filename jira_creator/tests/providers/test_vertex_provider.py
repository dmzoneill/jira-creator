#!/usr/bin/env python
"""
This file contains unit tests for the VertexAIProvider class in the providers.vertex_provider module.

It includes tests for the improve_text method, which interacts with Google Vertex AI to improve text
inputs using either Anthropic Claude or Google Gemini models. The tests cover scenarios where the API
calls are successful and when they fail, asserting the expected behavior in each case.

Functions:
- test_vertex_provider_detects_claude_model: Tests model type detection for Claude models
- test_vertex_provider_detects_gemini_model: Tests model type detection for Gemini models
- test_vertex_provider_rejects_invalid_model: Tests rejection of unsupported model types
- test_vertex_provider_claude_improve_text: Tests Claude text improvement functionality
- test_vertex_provider_gemini_improve_text: Tests Gemini text improvement functionality
- test_vertex_provider_claude_api_failure: Tests error handling for Claude API failures
- test_vertex_provider_gemini_api_failure: Tests error handling for Gemini API failures
- test_vertex_provider_claude_missing_dependency: Tests error handling when anthropic package missing
- test_vertex_provider_gemini_missing_dependency: Tests error handling when google-cloud package missing
- test_vertex_provider_uses_anthropic_project_id: Tests that Claude uses ANTHROPIC_VERTEX_PROJECT_ID

Exceptions:
- AiError: Raised if there is a failure when calling the Vertex AI API or configuration is invalid.

Side Effects:
- Mocks external SDK calls to Anthropic and Google Vertex AI
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from jira_creator.exceptions.exceptions import AiError
from jira_creator.providers.vertex_provider import VertexAIProvider


def test_vertex_provider_detects_claude_model():
    """
    Tests that the VertexAIProvider correctly detects Claude models based on model name prefix.

    This test verifies that when JIRA_AI_MODEL starts with "claude-", the provider sets
    model_type to "claude" and uses the appropriate project configuration.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks environment variables via EnvFetcher
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "my-claude-project",
            "GOOGLE_CLOUD_PROJECT": "my-general-project",
        }.get(key, default)

        provider = VertexAIProvider()
        assert provider.model_type == "claude"
        assert provider.model == "claude-3-5-sonnet@20241022"
        assert provider.project_id == "my-claude-project"
        assert provider.location == "us-central1"


def test_vertex_provider_detects_gemini_model():
    """
    Tests that the VertexAIProvider correctly detects Gemini models based on model name prefix.

    This test verifies that when JIRA_AI_MODEL starts with "gemini-", the provider sets
    model_type to "gemini" and uses the appropriate project configuration.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks environment variables via EnvFetcher
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "my-gemini-project",
        }.get(key, default)

        provider = VertexAIProvider()
        assert provider.model_type == "gemini"
        assert provider.model == "gemini-1.5-pro"
        assert provider.project_id == "my-gemini-project"
        assert provider.location == "us-central1"


def test_vertex_provider_rejects_invalid_model():
    """
    Tests that the VertexAIProvider rejects unsupported model types.

    This test verifies that when JIRA_AI_MODEL doesn't start with "claude-" or "gemini-",
    the provider raises an AiError during initialization.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks environment variables via EnvFetcher

    Exceptions:
    - AiError: Raised when model name is invalid
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gpt-4",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "my-project",
        }.get(key, default)

        with pytest.raises(AiError) as exc_info:
            VertexAIProvider()

        assert "Unsupported Vertex AI model" in str(exc_info.value)
        assert "gpt-4" in str(exc_info.value)


def test_vertex_provider_claude_improve_text():
    """
    Tests the VertexAIProvider's text improvement functionality with Claude models.

    This test mocks the AnthropicVertex client and verifies that the improve_text method
    correctly processes the response from Claude on Vertex AI.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks AnthropicVertex SDK
    - Mocks environment variables
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the Anthropic Vertex SDK
        mock_content = Mock()
        mock_content.text = "Improved text from Claude"

        mock_message = Mock()
        mock_message.content = [mock_content]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        # Create a mock anthropic module
        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        # Patch the import to return our mock module
        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            result = provider.improve_text("test prompt", "test input")

            assert result == "Improved text from Claude"
            mock_anthropic_module.AnthropicVertex.assert_called_once_with(
                region="us-central1", project_id="test-project"
            )
            mock_client.messages.create.assert_called_once()


def test_vertex_provider_gemini_improve_text():
    """
    Tests the VertexAIProvider's text improvement functionality with Gemini models.

    This test mocks the Vertex AI GenerativeModel and verifies that the improve_text method
    correctly processes the response from Gemini.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks Google Vertex AI SDK
    - Mocks environment variables
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the Vertex AI SDK
        mock_response = Mock()
        mock_response.text = "Improved text from Gemini"

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        # Create mock vertexai modules
        mock_generative_models = MagicMock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        mock_vertexai = MagicMock()
        mock_vertexai.generative_models = mock_generative_models

        # Patch the import to return our mock modules
        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            result = provider.improve_text("test prompt", "test input")

            assert result == "Improved text from Gemini"
            mock_vertexai.init.assert_called_once_with(project="test-project", location="us-central1")
            mock_generative_models.GenerativeModel.assert_called_once_with("gemini-1.5-pro")
            mock_model.generate_content.assert_called_once()


def test_vertex_provider_claude_api_failure():
    """
    Tests error handling when the Claude Vertex AI API call fails.

    This test verifies that the provider correctly raises an AiError when the
    Claude API encounters an error.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks AnthropicVertex SDK to raise an exception
    - Mocks environment variables

    Exceptions:
    - AiError: Raised when the Claude API call fails
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Create a mock anthropic module
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")

        mock_anthropic_module = MagicMock()
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        # Patch the import to return our mock module
        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(AiError) as exc_info:
                provider.improve_text("test prompt", "test input")

            assert "Claude Vertex AI call failed" in str(exc_info.value)


def test_vertex_provider_gemini_api_failure():
    """
    Tests error handling when the Gemini Vertex AI API call fails.

    This test verifies that the provider correctly raises an AiError when the
    Gemini API encounters an error.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks Google Vertex AI SDK to raise an exception
    - Mocks environment variables

    Exceptions:
    - AiError: Raised when the Gemini API call fails
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Create mock vertexai modules
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")

        mock_generative_models = MagicMock()
        mock_generative_models.GenerativeModel.return_value = mock_model

        mock_vertexai = MagicMock()
        mock_vertexai.generative_models = mock_generative_models

        # Patch the import to return our mock modules
        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            with pytest.raises(AiError) as exc_info:
                provider.improve_text("test prompt", "test input")

            assert "Gemini Vertex AI call failed" in str(exc_info.value)


def test_vertex_provider_claude_missing_dependency():
    """
    Tests error handling when the anthropic package is not installed.

    This test verifies that the provider raises an AiError with a helpful message
    when the anthropic[vertex] package is missing.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks ImportError for anthropic package

    Exceptions:
    - AiError: Raised when the anthropic package is not installed
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("No module named 'anthropic'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(AiError) as exc_info:
                provider.improve_text("test prompt", "test input")

            assert "anthropic[vertex] package not installed" in str(exc_info.value)


def test_vertex_provider_gemini_missing_dependency():
    """
    Tests error handling when the google-cloud-aiplatform package is not installed.

    This test verifies that the provider raises an AiError with a helpful message
    when the google-cloud-aiplatform package is missing.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks ImportError for google-cloud-aiplatform package

    Exceptions:
    - AiError: Raised when the google-cloud-aiplatform package is not installed
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "vertexai" in name:
                raise ImportError("No module named 'vertexai'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(AiError) as exc_info:
                provider.improve_text("test prompt", "test input")

            assert "google-cloud-aiplatform package not installed" in str(exc_info.value)


def test_vertex_provider_uses_anthropic_project_id():
    """
    Tests that Claude models prioritize ANTHROPIC_VERTEX_PROJECT_ID over GOOGLE_CLOUD_PROJECT.

    This test verifies that when using Claude models, the provider uses the
    ANTHROPIC_VERTEX_PROJECT_ID environment variable if available.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks environment variables
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "claude-specific-project",
            "GOOGLE_CLOUD_PROJECT": "general-project",
        }.get(key, default)

        provider = VertexAIProvider()
        assert provider.project_id == "claude-specific-project"


def test_vertex_provider_claude_fallback_to_gcp_project():
    """
    Tests that Claude models fall back to GOOGLE_CLOUD_PROJECT if ANTHROPIC_VERTEX_PROJECT_ID is not set.

    This test verifies that when ANTHROPIC_VERTEX_PROJECT_ID is not available,
    the provider falls back to using GOOGLE_CLOUD_PROJECT for Claude models.

    Arguments:
    - None

    Return:
    - None (assertion-based test)

    Side Effects:
    - Mocks environment variables
    """
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:

        def env_get(key, default=None):
            values = {
                "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
                "GOOGLE_CLOUD_LOCATION": "us-central1",
                "GOOGLE_CLOUD_PROJECT": "general-project",
            }
            # Simulate ANTHROPIC_VERTEX_PROJECT_ID not being set
            if key == "ANTHROPIC_VERTEX_PROJECT_ID":
                # Call the nested get for GOOGLE_CLOUD_PROJECT
                return env_get("GOOGLE_CLOUD_PROJECT", default)
            return values.get(key, default)

        mock_env.side_effect = env_get

        provider = VertexAIProvider()
        assert provider.project_id == "general-project"


def test_vertex_provider_claude_analyze_error():
    """Test Claude analyze_error method."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Error analysis result"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            result = provider.analyze_error("test prompt", '{"error": "test"}')
            assert result == "Error analysis result"


def test_vertex_provider_gemini_analyze_error():
    """Test Gemini analyze_error method."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini error analysis"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            result = provider.analyze_error("test prompt", '{"error": "test"}')
            assert result == "Gemini error analysis"


def test_vertex_provider_claude_analyze_and_fix_error():
    """Test Claude analyze_and_fix_error method."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"fix_type": "codebase", "confidence": 0.9}'
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            result = provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
            assert '{"fix_type": "codebase"' in result


def test_vertex_provider_gemini_analyze_and_fix_error():
    """Test Gemini analyze_and_fix_error method."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"fix_type": "payload", "confidence": 0.8}'
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            result = provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
            assert '{"fix_type": "payload"' in result


def test_vertex_provider_claude_analyze_error_empty_response():
    """Test Claude analyze_error with empty response."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex with empty content
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = []
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_error("test prompt", '{"error": "test"}')
            assert "Empty response" in str(exc_info.value)


def test_vertex_provider_claude_analyze_error_api_failure():
    """Test Claude analyze_error with API failure."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex with API failure
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_error("test prompt", '{"error": "test"}')
            assert "Claude Vertex AI call failed" in str(exc_info.value)


def test_vertex_provider_gemini_analyze_error_empty_response():
    """Test Gemini analyze_error with empty response."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules with empty response
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = None
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_error("test prompt", '{"error": "test"}')
            assert "Empty response" in str(exc_info.value)


def test_vertex_provider_gemini_analyze_error_api_failure():
    """Test Gemini analyze_error with API failure."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules with API failure
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_error("test prompt", '{"error": "test"}')
            assert "Gemini Vertex AI call failed" in str(exc_info.value)


def test_vertex_provider_claude_analyze_and_fix_error_empty_response():
    """Test Claude analyze_and_fix_error with empty response."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex with empty content
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = []
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
            assert "Empty response" in str(exc_info.value)


def test_vertex_provider_claude_analyze_and_fix_error_api_failure():
    """Test Claude analyze_and_fix_error with API failure."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex with API failure
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
            assert "Claude Vertex AI call failed" in str(exc_info.value)


def test_vertex_provider_gemini_analyze_and_fix_error_empty_response():
    """Test Gemini analyze_and_fix_error with empty response."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules with empty response
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = None
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
            assert "Empty response" in str(exc_info.value)


def test_vertex_provider_gemini_analyze_and_fix_error_api_failure():
    """Test Gemini analyze_and_fix_error with API failure."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules with API failure
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
            assert "Gemini Vertex AI call failed" in str(exc_info.value)


def test_vertex_provider_claude_improve_text_empty_response():
    """Test Claude improve_text with empty response."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Anthropic Vertex with empty content
        mock_anthropic_module = MagicMock()
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = []
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_module.AnthropicVertex.return_value = mock_client

        with patch.dict(sys.modules, {"anthropic": mock_anthropic_module}):
            with pytest.raises(AiError) as exc_info:
                provider.improve_text("test prompt", "test input")
            assert "Empty response" in str(exc_info.value)


def test_vertex_provider_gemini_improve_text_empty_response():
    """Test Gemini improve_text with empty response."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock Vertex AI modules with empty response
        mock_vertexai = MagicMock()
        mock_generative_models = MagicMock()
        mock_model_class = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = None
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        mock_generative_models.GenerativeModel = mock_model_class

        with patch.dict(sys.modules, {"vertexai": mock_vertexai, "vertexai.generative_models": mock_generative_models}):
            with pytest.raises(AiError) as exc_info:
                provider.improve_text("test prompt", "test input")
            assert "Empty response" in str(exc_info.value)


def test_vertex_provider_unknown_model_type_improve_text():
    """Test improve_text with unknown model type."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()
        # Manually set to unknown type to trigger the error path
        provider.model_type = "unknown"

        with pytest.raises(AiError) as exc_info:
            provider.improve_text("test prompt", "test input")
        assert "Unknown model type: unknown" in str(exc_info.value)


def test_vertex_provider_unknown_model_type_analyze_error():
    """Test analyze_error with unknown model type."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()
        # Manually set to unknown type to trigger the error path
        provider.model_type = "unknown"

        with pytest.raises(AiError) as exc_info:
            provider.analyze_error("test prompt", '{"error": "test"}')
        assert "Unknown model type: unknown" in str(exc_info.value)


def test_vertex_provider_unknown_model_type_analyze_and_fix_error():
    """Test analyze_and_fix_error with unknown model type."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()
        # Manually set to unknown type to trigger the error path
        provider.model_type = "unknown"

        with pytest.raises(AiError) as exc_info:
            provider.analyze_and_fix_error("test prompt", '{"error": "test"}')
        assert "Unknown model type: unknown" in str(exc_info.value)


def test_vertex_provider_claude_analyze_error_missing_dependency():
    """Test Claude analyze_error with missing anthropic dependency."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("No module named 'anthropic'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_error("test prompt", '{"error": "test"}')

            assert "anthropic[vertex] package not installed" in str(exc_info.value)


def test_vertex_provider_gemini_analyze_error_missing_dependency():
    """Test Gemini analyze_error with missing vertexai dependency."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "vertexai" in name:
                raise ImportError("No module named 'vertexai'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_error("test prompt", '{"error": "test"}')

            assert "google-cloud-aiplatform package not installed" in str(exc_info.value)


def test_vertex_provider_claude_analyze_and_fix_error_missing_dependency():
    """Test Claude analyze_and_fix_error with missing anthropic dependency."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "claude-3-5-sonnet@20241022",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "ANTHROPIC_VERTEX_PROJECT_ID": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("No module named 'anthropic'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_and_fix_error("test prompt", '{"error": "test"}')

            assert "anthropic[vertex] package not installed" in str(exc_info.value)


def test_vertex_provider_gemini_analyze_and_fix_error_missing_dependency():
    """Test Gemini analyze_and_fix_error with missing vertexai dependency."""
    with patch("jira_creator.providers.vertex_provider.EnvFetcher.get") as mock_env:
        mock_env.side_effect = lambda key, default=None: {
            "JIRA_AI_MODEL": "gemini-1.5-pro",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project",
        }.get(key, default)

        provider = VertexAIProvider()

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "vertexai" in name:
                raise ImportError("No module named 'vertexai'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(AiError) as exc_info:
                provider.analyze_and_fix_error("test prompt", '{"error": "test"}')

            assert "google-cloud-aiplatform package not installed" in str(exc_info.value)
