# jira-creator 📝

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds) 🚀

### 1. Create your config file and enable autocomplete 📝.

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
This config file sets all the necessary environment variables for operating the AI and JIRA API. Running these commands will create the config file and initialize it in the current shell.

### 2. Link the command-line tool wrapper 🖇️

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```
This command makes the shell script `rh-issue-wrapper.sh` executable and links it to a location in your `PATH`. You can then access the script anywhere from your command line by typing `rh-issue`.

### 3. Run it 🏃

```bash
rh-issue create story "Improve onboarding experience"
```
This command creates a new story issue in JIRA. The argument `"Improve onboarding experience"` is the title of the new issue.

## 🧪 Usage & Commands 🛠️

### 🆕 Create Issues

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

The `--edit` option opens your default `$EDITOR` for you to add additional details to the issue, and `--dry-run` prints the payload without actually creating the issue.

### 🔁 Change Issue Type

```bash
rh-issue change AAP-12345 story
```
This command changes the type of issue `AAP-12345` to `story`.

### 🔁 Migrate Issue

```bash
rh-issue migrate AAP-54321 story
```
This command migrates issue `AAP-54321` to a `story`. 

### ✏️ Edit Description

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```
These commands open the issue `AAP-98765` for editing, with or without AI assistance.

### 🧍 Unassign Issue

```bash
rh-issue unassign AAP-12345
```
This command unassigns the issue `AAP-12345`.

### 📋 List Issues

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```
These commands list all issues, or only those matching given criteria.

### 🏷️ Set Priority

```bash
rh-issue set-priority AAP-123 High
```
This command sets the priority of issue `AAP-123` to `High`.

### 📅 Sprint Management

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```
These commands manage the sprint assignment of issue `AAP-456`.

### 🚦 Set Status

```bash
rh-issue set-status AAP-123 "In Progress"
```
This command sets the status of issue `AAP-123` to `In Progress`.

## 🤖 AI Provider Support 

You can plug in different AI providers by setting `AI_PROVIDER`.

We can use ollama for the management for different models

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

## 🛠 Dev Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make format  # autofix formatting
```

## ⚙️ How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

## 📜 License

This project is licensed under the [Apache License](./LICENSE).