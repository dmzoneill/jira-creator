# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1️⃣ Create your config file and enable autocomplete

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
export JIRA_BOARD_ID=21125

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```
This sets up the environment for our tool. Replace the values with your own.

---

### 2️⃣ Link the command-line tool wrapper

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```
This makes the rh-issue command globally accessible.

---

### 3️⃣ Run it

```bash
rh-issue create story "Improve onboarding experience"
```
This creates a JIRA story with a given title.

---

## 🧪 Usage & Commands

### 🆕 Create Issues

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```
Create a variety of issue types including bugs, stories, epics, and spikes. Use `--edit` to use your `$EDITOR`, and `--dry-run` to print the payload without creating the issue.

### 🔁 Change Issue Type

```bash
rh-issue change AAP-12345 story
```
This changes the issue type to a story for the issue with the id `AAP-12345`.

### 🔀 Migrate Issue

```bash
rh-issue migrate AAP-54321 story
```
This migrates the issue with the id `AAP-54321` to a story.

### ✏️ Edit Description

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```
This edits the description of issue `AAP-98765` using AI or without AI if `--no-ai` is used.

### 🧍 Unassign Issue

```bash
rh-issue unassign AAP-12345
```
This unassigns the issue with the id `AAP-12345`.

### 📋 List Issues

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```
These commands list all issues or issues filtered by project, component, and user.

### 🏷️ Set Priority

```bash
rh-issue set-priority AAP-123 High
```
This sets the priority of issue `AAP-123` to high.

### 📅 Sprint Management

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```
These commands manage sprints of an issue `AAP-456`.

### 🚦 Set Status

```bash
rh-issue set-status AAP-123 "In Progress"
```
This sets the status of issue `AAP-123` to "In Progress".

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`.

### ✅ OpenAI

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional
```
This sets up OpenAI as the AI provider.

### 🖥 GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```
This sets up GPT4All as the AI provider.

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export INSTRUCTLAB_URL=http://localhost:11434/api/generate
export INSTRUCTLAB_MODEL=instructlab
```
This sets up InstructLab as the AI provider.

### 🧠 BART

```bash
export AI_PROVIDER=bart
export BART_URL=http://localhost:8000/bart
```
This sets up BART as the AI provider.

### 🧠 DeepSeek

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
docker compose exec ollama ollama pull deepseek-r1:7b
export AI_PROVIDER=deepseek
export DEEPSEEK_URL=http://localhost:11434/api/generate
```
This sets up DeepSeek as the AI provider.

### 🪫 Noop

```bash
export AI_PROVIDER=noop
```
This sets up Noop as the AI provider.

---

## 🛠 Dev Setup

```bash
pipenv install --dev
```
This sets up the development environment.

### Testing & Linting

```bash
make test
make lint
make format  # auto-fix formatting
```
These commands are for testing, linting, and formatting.

---

## ⚙️ How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).