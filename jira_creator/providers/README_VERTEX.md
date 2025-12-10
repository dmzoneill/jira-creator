# Vertex AI Provider

The Vertex AI provider enables jira-creator to use both **Anthropic Claude** and **Google Gemini** models running on Google Cloud Vertex AI.

## Features

- **Dual Model Support**: Automatically detects and routes to either Claude or Gemini based on model name
- **Google Cloud Authentication**: Uses Application Default Credentials (no API keys required)
- **Graceful Fallback**: Works even if SDK packages aren't installed (with helpful error messages)
- **Simple Configuration**: Just set environment variables and go

## Architecture

The `VertexAIProvider` class implements the `AIProvider` interface and provides intelligent routing:

- Models starting with `claude-` → Anthropic Vertex AI SDK
- Models starting with `gemini-` → Google Vertex AI SDK

## Prerequisites

### 1. Google Cloud CLI

Install and configure the Google Cloud CLI:

```bash
# Install gcloud CLI (if not already installed)
# See: https://cloud.google.com/sdk/docs/install

# Authenticate with Application Default Credentials
gcloud auth application-default login

# Set your default project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Python Dependencies

Install required packages:

```bash
# Install both Vertex AI SDKs
pipenv install

# Or manually:
pipenv install google-cloud-aiplatform 'anthropic[vertex]'
```

### 3. Google Cloud Permissions

Ensure your GCP account/service account has the following permissions:

**For Claude (Anthropic on Vertex):**
- `aiplatform.endpoints.predict`
- Access to Anthropic Claude models in Vertex AI

**For Gemini:**
- `aiplatform.endpoints.predict`
- Access to Gemini models in Vertex AI

## Configuration

### Environment Variables

#### Required for All Vertex AI Usage

```bash
export JIRA_AI_PROVIDER="vertex"
export JIRA_AI_MODEL="<model-name>"  # See model options below
export GOOGLE_CLOUD_LOCATION="us-central1"  # Or your preferred region
```

#### For Claude Models

```bash
export JIRA_AI_MODEL="claude-3-5-sonnet@20241022"
export ANTHROPIC_VERTEX_PROJECT_ID="your-gcp-project-id"

# Optional: If not set, falls back to GOOGLE_CLOUD_PROJECT
export GOOGLE_CLOUD_PROJECT="fallback-project-id"
```

#### For Gemini Models

```bash
export JIRA_AI_MODEL="gemini-1.5-pro"
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
```

### Available Models

#### Claude Models (Anthropic on Vertex AI)

- `claude-3-5-sonnet@20241022` - Claude 3.5 Sonnet (recommended)
- `claude-3-5-haiku@20241022` - Claude 3.5 Haiku (faster, cheaper)
- `claude-3-opus@20240229` - Claude 3 Opus (most capable)
- `claude-3-sonnet@20240229` - Claude 3 Sonnet
- `claude-3-haiku@20240307` - Claude 3 Haiku

Check [Anthropic's Vertex AI documentation](https://docs.anthropic.com/en/api/claude-on-vertex-ai) for the latest available models.

#### Gemini Models (Google Vertex AI)

- `gemini-1.5-pro` - Gemini 1.5 Pro (recommended)
- `gemini-1.5-flash` - Gemini 1.5 Flash (faster, cheaper)
- `gemini-1.0-pro` - Gemini 1.0 Pro

Check [Google's Vertex AI documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models) for the latest available models.

## Usage Examples

### Example 1: Using Claude on Vertex AI

```bash
# Set environment
export JIRA_AI_PROVIDER="vertex"
export JIRA_AI_MODEL="claude-3-5-sonnet@20241022"
export ANTHROPIC_VERTEX_PROJECT_ID="itpc-gcp-ansible-pe-eng-claude"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Create a JIRA issue with AI enhancement
rh-issue create-issue --type story --summary "Add user authentication"
```

### Example 2: Using Gemini on Vertex AI

```bash
# Set environment
export JIRA_AI_PROVIDER="vertex"
export JIRA_AI_MODEL="gemini-1.5-pro"
export GOOGLE_CLOUD_PROJECT="my-gcp-project"
export GOOGLE_CLOUD_LOCATION="us-central1"

# Create a JIRA issue with AI enhancement
rh-issue create-issue --type bug --summary "Fix login redirect issue"
```

### Example 3: Switching Between Models

```bash
# Use Claude for one command
JIRA_AI_MODEL="claude-3-5-sonnet@20241022" rh-issue lint --issue-key PROJ-123

# Use Gemini for another command
JIRA_AI_MODEL="gemini-1.5-pro" rh-issue set-acceptance-criteria --issue-key PROJ-456
```

## How It Works

### 1. Model Detection

On initialization, `VertexAIProvider` examines the `JIRA_AI_MODEL` environment variable:

```python
model_lower = self.model.lower()
if model_lower.startswith("claude"):
    self.model_type = "claude"
elif model_lower.startswith("gemini"):
    self.model_type = "gemini"
else:
    raise AiError("Unsupported Vertex AI model")
```

### 2. Authentication

Both SDKs use **Application Default Credentials (ADC)**, automatically configured via:

```bash
gcloud auth application-default login
```

No API keys are required. The SDKs handle authentication transparently.

### 3. API Calls

#### Claude (Anthropic Vertex SDK)

```python
from anthropic import AnthropicVertex

client = AnthropicVertex(
    region=self.location,
    project_id=self.project_id
)

message = client.messages.create(
    model=self.model,
    max_tokens=4096,
    temperature=0.8,
    messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}],
    system=prompt
)
```

#### Gemini (Google Vertex AI SDK)

```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=self.project_id, location=self.location)
model = GenerativeModel(self.model)

response = model.generate_content(
    f"{prompt}\n\n{text}",
    generation_config={
        "temperature": 0.8,
        "max_output_tokens": 4096
    }
)
```

## Error Handling

### Missing Dependencies

If the required SDK isn't installed, you'll see a helpful error:

```
⚠️ AI enhancement failed, using original text:
anthropic[vertex] package not installed. Run: pipenv install 'anthropic[vertex]'
```

The tool continues to work, just without AI enhancement.

### API Errors

API errors are caught and wrapped in `AiError`:

```python
try:
    # API call
except Exception as e:
    raise AiError(f"Claude Vertex AI call failed: {str(e)}") from e
```

This ensures the CLI remains functional even when AI services are unavailable.

## Testing

The provider includes comprehensive unit tests covering:

- Model type detection (Claude vs Gemini)
- Successful text improvement for both model types
- API failure scenarios
- Missing dependency handling
- Project ID configuration (ANTHROPIC_VERTEX_PROJECT_ID vs GOOGLE_CLOUD_PROJECT)

Run tests:

```bash
PYTHONPATH=.:jira_creator pipenv run pytest jira_creator/tests/providers/test_vertex_provider.py -v
```

## Cost Optimization

### Model Selection

Choose models based on your use case:

| Use Case | Recommended Model | Reason |
|----------|------------------|---------|
| Complex issues, high quality | `claude-3-5-sonnet@20241022` | Best balance of quality and cost |
| Simple issues, high volume | `claude-3-5-haiku@20241022` or `gemini-1.5-flash` | Faster, cheaper |
| Maximum quality | `claude-3-opus@20240229` | Most capable |

### Caching

The `LintPlugin` implements content-based caching using SHA-256 hashes, avoiding redundant API calls:

```python
# Located in ~/.config/rh-issue/ai-hashes.json
{
  "PROJ-123": {
    "summary_hash": "abc123...",
    "description_hash": "def456..."
  }
}
```

Only calls the AI API when content actually changes.

## Troubleshooting

### "No module named 'anthropic'" or "No module named 'vertexai'"

**Solution:** Install the missing dependencies:

```bash
pipenv install google-cloud-aiplatform 'anthropic[vertex]'
```

### "Unsupported Vertex AI model: gpt-4"

**Solution:** You're trying to use a non-Vertex model. Model names must start with `claude-` or `gemini-`.

### "Permission denied" or "403 Forbidden"

**Solution:** Check your GCP permissions:

```bash
# Re-authenticate
gcloud auth application-default login

# Verify project access
gcloud projects describe YOUR_PROJECT_ID

# Check IAM permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:user:YOUR_EMAIL"
```

### "Model not found" or "Invalid model"

**Solution:** The model may not be available in your region or project. Check:

1. Model availability in your region (some models are region-specific)
2. Vertex AI API is enabled: `gcloud services enable aiplatform.googleapis.com`
3. Model name/version is correct (check Vertex AI console)

## Regional Availability

Not all models are available in all regions. Common regions:

- `us-central1` - Most models available
- `us-east4` - Most models available
- `europe-west1` - Some models available
- `asia-southeast1` - Some models available

Check the Vertex AI console for your project to see which models are available in your region.

## Security Considerations

### Credential Management

- **Never commit credentials to git**
- Use `gcloud auth application-default login` for local development
- Use service accounts with minimal permissions for production
- Store service account keys securely (e.g., Google Secret Manager)

### Data Privacy

- Text sent to AI providers may be logged by Google Cloud
- Review your organization's data handling policies
- Consider data residency requirements when selecting regions

### Cost Control

- Set budget alerts in Google Cloud Console
- Monitor usage via Cloud Billing reports
- Use quotas to limit API usage if needed

## Migration from Other Providers

### From OpenAI

```bash
# Before
export JIRA_AI_PROVIDER="openai"
export JIRA_AI_API_KEY="sk-..."
export JIRA_AI_MODEL="gpt-4o-mini"

# After (Claude)
export JIRA_AI_PROVIDER="vertex"
export JIRA_AI_MODEL="claude-3-5-sonnet@20241022"
export ANTHROPIC_VERTEX_PROJECT_ID="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
# No API key needed!
```

### From DeepSeek/InstructLab

```bash
# Before
export JIRA_AI_PROVIDER="deepseek"
export JIRA_AI_URL="http://localhost:8080/v1/chat/completions"
export JIRA_AI_MODEL="deepseek-chat"

# After (Gemini)
export JIRA_AI_PROVIDER="vertex"
export JIRA_AI_MODEL="gemini-1.5-pro"
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

## Additional Resources

- [Anthropic Claude on Vertex AI Documentation](https://docs.anthropic.com/en/api/claude-on-vertex-ai)
- [Google Vertex AI Generative AI Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/overview)
- [Google Cloud SDK Installation](https://cloud.google.com/sdk/docs/install)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)

## Support

For issues or questions:

1. Check this README
2. Review test cases in `tests/providers/test_vertex_provider.py`
3. Check provider implementation in `vertex_provider.py`
4. File an issue on the project repository
