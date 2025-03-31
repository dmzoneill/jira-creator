# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

A command-line interface (CLI) tool to create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. 🛠️ Configuration and Autocomplete Setup

Create an environment variables file to store your JIRA settings. We enable autocomplete for improved command-line interaction.

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
eval "$(register-python-argcomplete rh-issue)"
EOF

source ~/.bashrc.d/jira.sh
```

---

### 2. 📡 CLI Wrapper Linking

Link the CLI wrapper for easier access:

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 3. 🏃‍♂️ Run the Tool

Run the tool with a command to create an issue:

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

Below are the basic commands and examples of how to use the jira-creator.

### 🆕 Create Issues

Different types of issues can be created such as bugs, stories, epics, and spikes. Use the `--edit` flag to open the issue in your `$EDITOR`, and `--dry-run` to print the payload without actually creating the issue.

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

### 🔁 Changing and Migrating Issues

Change the issue type or migrate an issue from one type to another:

```bash
rh-issue change AAP-12345 story
rh-issue migrate AAP-54321 story
```

### ✏️ Editing Issue Descriptions

Edit the description of an issue. Use the `--no-ai` flag to bypass the AI provider:

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🧍 Unassigning Issues

Unassign an issue from a user:

```bash
rh-issue unassign AAP-12345
```

### 📋 Listing Issues

List issues, optionally filtered by project, component, and user:

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Setting Issue Priority

Set priority of an issue:

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

Manage sprints by setting, removing, or adding: 

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Changing Issue Status

Change the status of an issue:

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

Plug in different AI providers by changing the `AI_PROVIDER` variable. Below are different AI providers supported:

### ✅ OpenAI

For OpenAI, provide the API key:

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional
```

### 🖥 GPT4All

For GPT4All, install the library and set the provider:

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```

### 🧪 And many more...

Check the README for a full list of supported providers and their setup instructions.

---

## 🛠 Dev Setup

To set up your development environment:

```bash
pipenv install --dev
```

### Testing & Linting

Run tests, linting, and auto-fix formatting issues:

```bash
make test
make lint
make format  # auto-fix formatting
```

---

## ⚙️ How It Works

jira-creator works by:
- Loading field definitions from `.tmpl` files under `templates/`
- Using `TemplateLoader` to generate Markdown descriptions
- Optionally applying AI cleanup for readability and structure
- Sending the data to JIRA via REST API (or dry-runs it)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).