# jira-creator

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. Create your config file:

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

## 🚀 Full Usage

```bash
rh-issue bug "Fix login crash"
rh-issue epic "Prepare Q2 milestone" --dry-run
```

---

## 🔧 Dev Setup

```bash
pip install pipenv
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
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