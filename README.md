# jira-creator

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. Create your config file and autocomplete setup:

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
export JPAT="your_jira_personal_access_token"
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export JIRA_URL="https://issues.redhat.com"
export PROJECT_KEY="AAP"
export AFFECTS_VERSION="aa-latest"
export COMPONENT_NAME="analytics-hcc-service"
export PRIORITY="Normal"

# Enable autocomplete
eval "$(register-python-argcomplete rh-issue)"
EOF

source ~/.bashrc.d/jira.sh
```

---

### 2. Link the CLI wrapper:

```bash
chmod +x rh-issue-wrapper.sh
sudo ln -s $(pwd)/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 3. Run it:

```bash
rh-issue story "Improve onboarding experience"
```

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting the `AI_PROVIDER` environment variable.

### ✅ OpenAI (via REST API)

- Uses direct HTTP request to OpenAI’s `/v1/chat/completions` endpoint (no SDK needed)
- Set up:

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-4
```

---

### 🖥️ GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```

---

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export INSTRUCTLAB_URL=http://localhost:11434/api/generate
export INSTRUCTLAB_MODEL=instructlab
```

---

### 🧠 BART

```bash
export AI_PROVIDER=bart
export BART_URL=http://localhost:8000/bart
```

---

### 🧠 DeepSeek

```bash
export AI_PROVIDER=deepseek
export DEEPSEEK_URL=http://localhost:8000/deepseek
```

---

### 🪫 Noop (fallback)

Returns the input unchanged:

```bash
export AI_PROVIDER=noop
```

---

## 🔧 Dev Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
```

To automatically fix formatting issues:

```bash
make format
```

---

## 🛠️ How It Works

- Prompts for input fields defined in a per-type `.tmpl` file under `templates/`
- Uses `TemplateLoader` to render the issue description
- Optionally passes the text through an AI provider for grammar/readability
- Sends the issue to JIRA via REST API (or prints in dry-run mode)

---

## 📂 File Structure

```
jira-creator/
├── rh-jira.py
├── rh-issue-wrapper.sh
├── templates/
├── providers/
├── jira/
├── tests/
└── Pipfile
```
---

## 🧪 Usage & Examples

### 🆕 Create Issues

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

Use `--edit` to fill the issue description using your `$EDITOR`  
Use `--dry-run` to print the payload without sending it to JIRA

---

### 🔁 Change Issue Type

```bash
rh-issue change-type AAP-12345 story
```

Converts an issue (e.g. sub-task) into another type (e.g. story). If it is a sub-task, the parent field is removed automatically.

---

### 🔁 Migrate Issue

```bash
rh-issue migrate-to story AAP-54321
```

Copies the issue, creates a new one as a different type, adds a backlink comment to the old one, and closes the old issue.

---

### ✏️ Edit Issue Description

```bash
rh-issue edit-issue AAP-98765
rh-issue edit-issue AAP-98765 --no-ai
```

- Fetches the description
- Opens it in your editor (`$EDITOR`)
- Applies AI cleanup (unless `--no-ai` is used)
- Updates the JIRA issue