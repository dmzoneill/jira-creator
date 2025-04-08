# 🛠️ jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

A powerful command-line tool for creating JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates, and optional AI-enhanced descriptions.

---

## 🚀 Quick Start (Under 30 Seconds)

### 1️⃣ Create your config file and enable autocomplete

First, we set up a configuration file `jira.sh` with our JIRA credentials, AI settings and project information.

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
export JIRA_EPIC_FIELD="customfield_12311140"
export JIRA_ACCEPTANCE_CRITERIA_FIELD="customfield_12315940"
export JIRA_BLOCKED_FIELD="customfield_12316543"
export JIRA_BLOCKED_REASON_FIELD="customfield_12316544"
export JIRA_STORY_POINTS_FIELD="customfield_12310243"
export JIRA_SPRINT_FIELD="customfield_12310940"

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

---

### 2️⃣ Link the command-line tool wrapper

Next, we make the tool executable and link it to a convenient location in our PATH.

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 3️⃣ Run it

Finally, let's test our setup by creating a story in JIRA.

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 📘 Usage & Commands

Here are some common commands you can use with `rh-issue`.

### 🆕 Create Issues

You can create various types of issues including bug, story, epic, and spike.

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

Use `--edit` to open the issue in your `$EDITOR`, and `--dry-run` to print the payload without creating the issue.

### 🔄 Change Issue Type

To change the type of an existing issue use:

```bash
rh-issue change AAP-12345 story
```

### 🚚 Migrate Issue

To migrate an issue to a different project or issue type:

```bash
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

To edit the description of an existing issue, use:

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

Use `--no-ai` to disable the AI enhancements while editing.

### 🧍 Unassign Issue

To unassign a user from an issue, use:

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

List all issues or filter by project, component, or user:

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

To change the priority of an issue, use:

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

Manage sprint assignments for an issue:

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

Change the status of an issue:

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

You can use various AI providers by setting `AI_PROVIDER`. You can manage different AI models using ollama:

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

For each AI provider, set `AI_PROVIDER` and other environment variables as described below:

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

### 🖥 GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=instructlab
```

### 🧠 BART

```bash
export AI_PROVIDER=bart
export AI_URL=http://localhost:8000/bart
```

### 🪫 Noop

```bash
export AI_PROVIDER=noop
```

---

## 🔧 Dev Setup

Install development dependencies:

```bash
pipenv install --dev
```

### Testing & Linting

To test, lint, and format the code:

```bash
make test
make lint
make format  # autofix formatting
```

---

## ⚙️ How It Works

- The tool loads field definitions from `.tmpl` files under `templates/`
- It uses `TemplateLoader` to generate Markdown descriptions
- It applies AI cleanup for readability and structure
- The tool sends the issue details to JIRA via REST API (or performs a dry-run if requested)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).