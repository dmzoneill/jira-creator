# 🛠 jira-creator

![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)
![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)

Generate JIRA issues (stories, bugs, epics, spikes, tasks) swiftly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. Configure Your Settings and Enable Autocomplete

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
export JPAT="your_jira_personal_access_token"
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL="gpt-4o-mini"
export JIRA_URL="https://issues.redhat.com"
export PROJECT_KEY="AAP"
export AFFECTS_VERSION="aa-latest"
export COMPONENT_NAME="analytics-hcc-service"
export PRIORITY="Normal"
export JIRA_BOARD_ID=21125

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```
---

### 2. Connect the Command-Line Tool Wrapper

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 3. Execute It

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

### 🆕 Issue Creation

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

Use `--edit` to use your `$EDITOR`, and `--dry-run` to display the payload without creating the issue.

### 🔁 Change Issue Type

```bash
rh-issue change AAP-12345 story
```

### 🔀 Migrate Issue

```bash
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🧍 Unassign Issue

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Assign Priority

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Status Assignment

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Setup

You can integrate different AI providers by setting `AI_PROVIDER`.

Use ollama for the management of different models

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

### ✅ OpenAI

```bash
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL=gpt-4  # Optional
```

### 🦙 LLama3

```bash
docker compose exec ollama ollama pull LLama3
export AI_PROVIDER=LLama3
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=LLama3
```

### 🧠 DeepSeek

```bash
docker compose exec ollama ollama pull deepseek-r1:7b
export AI_PROVIDER=deepseek
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=http://localhost:11434/api/generate
```

---

## 🛠 Development Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make format  # autofix formatting
```

---

## ⚙️ How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Utilizes `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).