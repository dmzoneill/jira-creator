# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Effortlessly generate JIRA issues such as stories, bugs, epics, spikes, and tasks employing predefined templates and optional AI-boosted descriptions.

---

## ⚡ Quick Start Guide (Under 30 Seconds)

### 1. Config File Creation and Autocomplete Activation

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
export JIRA_JPAT="your_jira_personal_access_token"
export JIRA_AI_PROVIDER=openai
export JIRA_AI_API_KEY=sk-...
export JIRA_AI_MODEL="gpt-4o-mini"
export JIRA_URL="https://issues.redhat.com"
export JIRA_PROJECT_KEY="AAP"
export JIRA_AFFECTS_VERSION="aa-latest"
export JIRA_COMPONENT_NAME="analytics-hcc-service"
export JIRA_PRIORITY="Normal"
export JIRA_BOARD_ID=21125
export JIRA_EPIC_FIELD="customfield_12311140"
export JIRA_ACCEPTANCE_CRITERIA_FIELD="customfield_12315940"
export JIRA_BLOCKED_FIELD="customfield_12316543"
export JIRA_BLOCKED_REASON_FIELD="customfield_12316544"
export JIRA_STORY_POINTS_FIELD="customfield_12310243"
export JIRA_SPRINT_FIELD="customfield_12310940"
export JIRA_VOSK_MODEL="/home/daoneill/.vosk/vosk-model-small-en-us-0.15"

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

---

### 2. Command-line Tool Wrapper Link Creation

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 3. Execute the Program

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

This document describes the various commands that can be used to manage JIRA issues from the command-line.

## :mag_right: Search Issues

The `search` command allows you to find issues using a JIRA Query Language (JQL) expression.

**Example:**

```bash
search "project = 'PROJ' AND status = 'In Progress'"
```

## :page_with_curl: List Issues

The `list-issues` command retrieves a list of all issues in a specific project, with options to filter by component, assignee, status, summary and reporter. You can customize the output by specifying the columns to show and the order to sort them.

**Example:**

```bash
list-issues --project 'PROJ' --status 'In Progress' --columns 'key, summary, status' --sort 'key'
```

## :beetle: Create Issue

The `create-issue` command is used to create a new issue. You can specify the type of the issue (bug, story, epic, task, spike) and its summary. The `--edit` flag allows you to modify the issue before it's created, while the `--dry-run` flag simulates the issue creation without actually doing it.

**Example:**

```bash
create-issue --type bug --summary "This is a test bug"
```

## :pencil: Edit Issue

The `edit-issue` command allows you to modify an existing issue. The issue to edit is specified by its key. The `--no-ai` flag can be used to disable AI assistance during editing.

**Example:**

```bash
edit-issue --issue_key PROJ-123
```

## :inbox_tray: Set Priority

The `set-priority` command allows you to change the priority of an issue. You can specify the issue by its key and set the priority to normal, major or critical.

**Example:**

```bash
set-priority --issue_key PROJ-123 --priority major
```

## :chart_with_upwards_trend: Set Story Epic

The `set-story-epic` command links a story issue to an epic issue. Both the story issue and the epic issue are specified by their keys.

**Example:**

```bash
set-story-epic --issue_key PROJ-123 --epic_key PROJ-124
```

## :lock: Block and Unblock Issue

The `block` command allows you to block an issue, specifying the reason for the block. The `unblock` command removes the block from an issue. Both commands require the key of the issue.

**Example:**

```bash
block --issue_key PROJ-123 --reason "Waiting for PROJ-124"
unblock --issue_key PROJ-123
```

And many more...

Review each command and arguments to understand the depth of each command, and how it can be used to manage Jira issues effectively. It is recommended to always use the `--dry-run` flag when unsure about a command's effect.

---

## 🤖 AI Provider Support

You have the option to integrate different AI providers by modifying `JIRA_AI_PROVIDER`. Ollama can be employed to manage various models.

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

### ✅ OpenAI

```bash
export JIRA_AI_PROVIDER=openai
export JIRA_AI_API_KEY=sk-...
export JIRA_AI_MODEL=gpt-4  # Optional
```

### 🦙 LLama3

```bash
docker compose exec ollama ollama pull LLama3
export JIRA_AI_PROVIDER=LLama3
export JIRA_AI_URL=http://localhost:11434/api/generate
export JIRA_AI_MODEL=LLama3
```

### 🧠 DeepSeek

```bash
docker compose exec ollama ollama pull deepseek-r1:7b
export JIRA_AI_PROVIDER=deepseek
export JIRA_AI_URL=http://localhost:11434/api/generate
export JIRA_AI_MODEL=http://localhost:11434/api/generate
```

### 🖥 GPT4All

```bash
pip install gpt4all
export JIRA_AI_PROVIDER=gpt4all
# WIP
```

### 🧪 InstructLab

```bash
export JIRA_AI_PROVIDER=instructlab
export JIRA_AI_URL=http://localhost:11434/api/generate
export JIRA_AI_MODEL=instructlab
# WIP
```

### 🧠 BART

```bash
export JIRA_AI_PROVIDER=bart
export JIRA_AI_URL=http://localhost:8000/bart
# WIP
```

### 🪫 Noop

```bash
export JIRA_AI_PROVIDER=noop
```

---

## 🛠 Developer Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make super-lint
```

---

## ⚙️ Functionality Overview

- The tool gathers field definitions from `.tmpl` files located under `templates/`
- Employs `TemplateLoader` for generating Markdown descriptions
- Optionally applies AI for enhancing readability and structure
- Sends to JIRA through REST API (or performs a dry run)

---

## 📜 License

This project falls under the terms of the [Apache License](./LICENSE).