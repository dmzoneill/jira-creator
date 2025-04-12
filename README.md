# jira-creator 📝

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds) ⏱️

### 1. Create your config file and enable autocomplete. 💻

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
export VOSK_MODEL="/home/daoneill/.vosk/vosk-model-small-en-us-0.15"

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

### 2. Link the command-line tool wrapper 🖇️

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 3. Run it 🚀

```bash
rh-issue create story "Improve onboarding experience"
```
---

## 🧪 Usage & Commands 🛠️

### 🆕 Create Issues

Use the `create` command followed by the issue type (bug, story, epic, spike) and the description.

Use `--edit` to use your `$EDITOR`, and `--dry-run` to print the payload without creating the issue.

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

### 🔁 Change Issue Type

To change an issue type, use the `change` command, followed by the issue key and the new type.

```bash
rh-issue change AAP-12345 story
```

### 📦 Migrate Issue

To migrate an issue, use the `migrate` command followed by the issue key and the new type.

```bash
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

To edit the description of an issue, use the `edit` command and the issue key. Use `--no-ai` to disable AI enhancement.

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🧍 Unassign Issue

To unassign an issue, use the `unassign` command followed by the issue key.

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

To list issues, use the `list` command. You can filter by project, component, and user.

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

To set the priority of an issue, use the `set-priority` command, followed by the issue key and the new priority.

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

To manage sprints, use the `set-sprint`, `remove-sprint`, and `add-sprint` commands followed by the issue key and the sprint details.

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

To set the status of an issue, use the `set-status` command, followed by the issue key and the new status.

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support 🧠

You can plug in different AI providers by setting `AI_PROVIDER`.

Check out the following examples of setting up different AI providers:

### ✅ OpenAI

To use OpenAI, set your `AI_API_KEY` and optionally specify an `AI_MODEL`.

```bash
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL=gpt-4  # Optional
```

### 🦙 LLama3

To use LLama3, first pull the model using Docker, then specify the provider, URL, and model.

```bash
docker compose exec ollama ollama pull LLama3
export AI_PROVIDER=LLama3
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=LLama3
```

### 🧠 DeepSeek

To use DeepSeek, first pull the model using Docker, then specify the provider, URL, and model.

```bash
docker compose exec ollama ollama pull deepseek-r1:7b
export AI_PROVIDER=deepseek
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=http://localhost:11434/api/generate
```

### 🖥 GPT4All

To use GPT4All, install the package via pip and set the provider.

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
# WIP
```

### 🧪 InstructLab

To use InstructLab, specify the provider, URL, and model.

```bash
export AI_PROVIDER=instructlab
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=instructlab
# WIP
```

### 🧠 BART

To use BART, specify the provider and URL.

```bash
export AI_PROVIDER=bart
export AI_URL=http://localhost:8000/bart
# WIP
```

### 🪫 Noop

To disable AI enhancement, set the provider as `noop`.

```bash
export AI_PROVIDER=noop
```

---

## 🛠 Dev Setup ⚙️

Install the development dependencies with pipenv.

```bash
pipenv install --dev
```

### Testing & Linting

Run tests, linting, and autofix code formatting with Make.

```bash
make test
make lint
make format  # autofix formatting
```

---

## ⚙️ How It Works 📜

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

---

## 📜 License 📚

This project is licensed under the [Apache License](./LICENSE).