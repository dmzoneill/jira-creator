#!/usr/bin/env python
"""
This module provides the VertexAIProvider class for interacting with Google Vertex AI.

The VertexAIProvider supports both Anthropic Claude models and Google Gemini models running on
Vertex AI. It automatically detects which backend to use based on the model name prefix:
- Models starting with "claude-" use the Anthropic Vertex AI SDK
- Models starting with "gemini-" use the Google Vertex AI SDK

The provider leverages Google Cloud CLI authentication (Application Default Credentials) and
requires appropriate environment variables to be set for project and location configuration.

Classes:
- VertexAIProvider: A class for managing interactions with Vertex AI models.

Attributes of VertexAIProvider:
- project_id (str): The GCP project ID for Vertex AI.
- location (str): The GCP region/location (e.g., us-central1).
- model (str): The model identifier (e.g., claude-3-5-sonnet@20241022, gemini-1.5-pro).
- model_type (str): Detected model type ('claude' or 'gemini').

Methods:
- improve_text(prompt: str, text: str) -> str:
  Sends a request to Vertex AI to improve the text based on the prompt.

Exceptions:
- AiError: Raised when the Vertex AI API call fails or configuration is invalid.
"""

# pylint: disable=too-few-public-methods

import warnings

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import AiError
from jira_creator.providers.ai_provider import AIProvider

# Suppress Google Auth quota project warning for ADC credentials
warnings.filterwarnings(
    "ignore", message=".*end user credentials.*quota project.*", category=UserWarning, module="google.auth._default"
)


class VertexAIProvider(AIProvider):
    """
    A class that provides methods to interact with Google Vertex AI.

    This provider supports both Anthropic Claude and Google Gemini models running on Vertex AI.
    It automatically detects which SDK to use based on the model name prefix.

    Attributes:
    - project_id (str): The GCP project ID for Vertex AI.
    - location (str): The GCP region/location (e.g., us-central1).
    - model (str): The model identifier.
    - model_type (str): The detected model type ('claude' or 'gemini').
    """

    def __init__(self) -> None:
        """
        Initialize the VertexAIProvider with configuration from environment variables.

        This method detects the model type and configures the appropriate settings for
        either Claude (Anthropic) or Gemini models on Vertex AI.

        Environment Variables:
        - JIRA_AI_MODEL: The model name (e.g., "claude-3-5-sonnet@20241022" or "gemini-1.5-pro")
        - GOOGLE_CLOUD_LOCATION: GCP region (e.g., "us-central1")
        - ANTHROPIC_VERTEX_PROJECT_ID: GCP project ID for Claude models (optional)
        - GOOGLE_CLOUD_PROJECT: GCP project ID for Gemini models (fallback)

        Side Effects:
        - Sets model, project_id, location, and model_type attributes
        - Raises AiError if required dependencies are missing

        Exceptions:
        - AiError: If required Python packages are not installed or model type is unsupported
        """
        self.model: str = EnvFetcher.get("JIRA_AI_MODEL")
        self.location: str = EnvFetcher.get("GOOGLE_CLOUD_LOCATION", "us-central1")

        # Detect model type based on model name prefix
        model_lower = self.model.lower()
        if model_lower.startswith("claude"):
            self.model_type = "claude"
            # Use Anthropic project ID if set, fallback to general GCP project
            self.project_id: str = EnvFetcher.get("ANTHROPIC_VERTEX_PROJECT_ID", EnvFetcher.get("GOOGLE_CLOUD_PROJECT"))
        elif model_lower.startswith("gemini"):
            self.model_type = "gemini"
            self.project_id: str = EnvFetcher.get("GOOGLE_CLOUD_PROJECT")
        else:
            raise AiError(f"Unsupported Vertex AI model: {self.model}. Model must start with 'claude-' or 'gemini-'")

    def improve_text(self, prompt: str, text: str) -> str:
        """
        Improves the given text using Vertex AI (Claude or Gemini).

        This method routes the request to either the Anthropic Vertex SDK or Google Vertex SDK
        based on the detected model type.

        Arguments:
        - prompt (str): The system prompt providing context for improving the text.
        - text (str): The user text to be improved.

        Return:
        - str: The improved text after processing with Vertex AI.

        Side Effects:
        - Makes a request to Vertex AI using the appropriate SDK.

        Exceptions:
        - AiError: Raised when the Vertex AI API call fails or dependencies are missing.
        """
        if self.model_type == "claude":
            return self._improve_with_claude(prompt, text)
        if self.model_type == "gemini":
            return self._improve_with_gemini(prompt, text)
        raise AiError(f"Unknown model type: {self.model_type}")

    def _improve_with_claude(self, prompt: str, text: str) -> str:
        """
        Improve text using Anthropic Claude models on Vertex AI.

        Arguments:
        - prompt (str): The system prompt.
        - text (str): The user text to improve.

        Return:
        - str: The improved text.

        Exceptions:
        - AiError: If the anthropic package is not installed or API call fails.
        """
        try:
            from anthropic import AnthropicVertex
        except ImportError as e:
            raise AiError("anthropic[vertex] package not installed. Run: pipenv install 'anthropic[vertex]'") from e

        try:
            client = AnthropicVertex(region=self.location, project_id=self.project_id)

            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.8,
                messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}],
                system=prompt if prompt else None,
            )

            # Extract text content from response
            content_blocks = message.content
            if content_blocks and len(content_blocks) > 0:
                raw_content = content_blocks[0].text
                return self.extract_content(raw_content)
            raise AiError("Empty response from Claude Vertex AI")

        except Exception as e:
            raise AiError(f"Claude Vertex AI call failed: {str(e)}") from e

    def _improve_with_gemini(self, prompt: str, text: str) -> str:
        """
        Improve text using Google Gemini models on Vertex AI.

        Arguments:
        - prompt (str): The system prompt/context.
        - text (str): The user text to improve.

        Return:
        - str: The improved text.

        Exceptions:
        - AiError: If the google-cloud-aiplatform package is not installed or API call fails.
        """
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
        except ImportError as e:
            raise AiError(
                "google-cloud-aiplatform package not installed. Run: pipenv install google-cloud-aiplatform"
            ) from e

        try:
            # Initialize Vertex AI SDK
            vertexai.init(project=self.project_id, location=self.location)

            # Create the model
            model = GenerativeModel(self.model)

            # Combine prompt and text
            full_prompt = f"{prompt}\n\n{text}"

            # Generate content
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.8,
                    "max_output_tokens": 4096,
                },
            )

            if response.text:
                return self.extract_content(response.text)
            raise AiError("Empty response from Gemini Vertex AI")

        except Exception as e:
            raise AiError(f"Gemini Vertex AI call failed: {str(e)}") from e

    def analyze_error(self, prompt: str, error_context: str) -> str:
        """
        Analyze a JIRA API error and suggest code-level fixes.

        This method routes the request to either the Anthropic Vertex SDK or Google Vertex SDK
        based on the detected model type.

        Arguments:
        - prompt (str): The system prompt for error analysis.
        - error_context (str): JSON-formatted error context.

        Return:
        - str: Markdown-formatted analysis with root cause, proposed fix, and workarounds.

        Exceptions:
        - AiError: Raised when the Vertex AI API call fails or dependencies are missing.
        """
        if self.model_type == "claude":
            return self._analyze_error_with_claude(prompt, error_context)
        if self.model_type == "gemini":
            return self._analyze_error_with_gemini(prompt, error_context)
        raise AiError(f"Unknown model type: {self.model_type}")

    def _analyze_error_with_claude(self, prompt: str, error_context: str) -> str:
        """
        Analyze error using Anthropic Claude models on Vertex AI.

        Arguments:
        - prompt (str): The system prompt for error analysis.
        - error_context (str): JSON-formatted error context.

        Return:
        - str: Markdown-formatted analysis.

        Exceptions:
        - AiError: If the anthropic package is not installed or API call fails.
        """
        try:
            from anthropic import AnthropicVertex
        except ImportError as e:
            raise AiError("anthropic[vertex] package not installed. Run: pipenv install 'anthropic[vertex]'") from e

        try:
            client = AnthropicVertex(region=self.location, project_id=self.project_id)

            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # Lower temperature for more deterministic analysis
                messages=[{"role": "user", "content": f"Analyze this error:\n\n{error_context}"}],
                system=prompt if prompt else None,
            )

            # Extract text content from response
            content_blocks = message.content
            if content_blocks and len(content_blocks) > 0:
                return content_blocks[0].text.strip()
            raise AiError("Empty response from Claude Vertex AI")

        except Exception as e:
            raise AiError(f"Claude Vertex AI call failed: {str(e)}") from e

    def _analyze_error_with_gemini(self, prompt: str, error_context: str) -> str:
        """
        Analyze error using Google Gemini models on Vertex AI.

        Arguments:
        - prompt (str): The system prompt for error analysis.
        - error_context (str): JSON-formatted error context.

        Return:
        - str: Markdown-formatted analysis.

        Exceptions:
        - AiError: If the google-cloud-aiplatform package is not installed or API call fails.
        """
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
        except ImportError as e:
            raise AiError(
                "google-cloud-aiplatform package not installed. Run: pipenv install google-cloud-aiplatform"
            ) from e

        try:
            # Initialize Vertex AI SDK
            vertexai.init(project=self.project_id, location=self.location)

            # Create the model
            model = GenerativeModel(self.model)

            # Combine prompt and error context
            full_prompt = f"{prompt}\n\nAnalyze this error:\n\n{error_context}"

            # Generate content
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temperature for more deterministic analysis
                    "max_output_tokens": 4096,
                },
            )

            if response.text:
                return response.text.strip()
            raise AiError("Empty response from Gemini Vertex AI")

        except Exception as e:
            raise AiError(f"Gemini Vertex AI call failed: {str(e)}") from e

    def analyze_and_fix_error(self, prompt: str, error_context: str) -> str:
        """
        Analyze an error and return a structured fix proposal in JSON format.

        This method routes the request to either the Anthropic Vertex SDK or Google Vertex SDK
        based on the detected model type.

        Arguments:
        - prompt (str): The system prompt for error analysis and fix generation.
        - error_context (str): JSON-formatted error context.

        Return:
        - str: JSON-formatted fix proposal.

        Exceptions:
        - AiError: Raised when the Vertex AI API call fails or dependencies are missing.
        """
        if self.model_type == "claude":
            return self._analyze_and_fix_with_claude(prompt, error_context)
        if self.model_type == "gemini":
            return self._analyze_and_fix_with_gemini(prompt, error_context)
        raise AiError(f"Unknown model type: {self.model_type}")

    def _analyze_and_fix_with_claude(self, prompt: str, error_context: str) -> str:
        """
        Analyze error and propose fix using Anthropic Claude models on Vertex AI.

        Arguments:
        - prompt (str): The system prompt for error analysis and fix generation.
        - error_context (str): JSON-formatted error context.

        Return:
        - str: JSON-formatted fix proposal.

        Exceptions:
        - AiError: If the anthropic package is not installed or API call fails.
        """
        try:
            from anthropic import AnthropicVertex
        except ImportError as e:
            raise AiError("anthropic[vertex] package not installed. Run: pipenv install 'anthropic[vertex]'") from e

        try:
            client = AnthropicVertex(region=self.location, project_id=self.project_id)

            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # Lower temperature for more deterministic analysis
                messages=[{"role": "user", "content": f"Analyze this error and propose a fix:\n\n{error_context}"}],
                system=prompt if prompt else None,
            )

            # Extract text content from response
            content_blocks = message.content
            if content_blocks and len(content_blocks) > 0:
                return content_blocks[0].text.strip()
            raise AiError("Empty response from Claude Vertex AI")

        except Exception as e:
            raise AiError(f"Claude Vertex AI call failed: {str(e)}") from e

    def _analyze_and_fix_with_gemini(self, prompt: str, error_context: str) -> str:
        """
        Analyze error and propose fix using Google Gemini models on Vertex AI.

        Arguments:
        - prompt (str): The system prompt for error analysis and fix generation.
        - error_context (str): JSON-formatted error context.

        Return:
        - str: JSON-formatted fix proposal.

        Exceptions:
        - AiError: If the google-cloud-aiplatform package is not installed or API call fails.
        """
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
        except ImportError as e:
            raise AiError(
                "google-cloud-aiplatform package not installed. Run: pipenv install google-cloud-aiplatform"
            ) from e

        try:
            # Initialize Vertex AI SDK
            vertexai.init(project=self.project_id, location=self.location)

            # Create the model
            model = GenerativeModel(self.model)

            # Combine prompt and error context
            full_prompt = f"{prompt}\n\nAnalyze this error and propose a fix:\n\n{error_context}"

            # Generate content
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temperature for more deterministic analysis
                    "max_output_tokens": 4096,
                },
            )

            if response.text:
                return response.text.strip()
            raise AiError("Empty response from Gemini Vertex AI")

        except Exception as e:
            raise AiError(f"Gemini Vertex AI call failed: {str(e)}") from e
