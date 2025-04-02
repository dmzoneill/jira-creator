# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Jira-creator is a command-line tool that allows you to create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 📁 1. Create your config file and enable autocomplete

The configuration file includes all the necessary environment variables for the jira-creator. Remember to replace the placeholders with your actual Jira credentials, project details, and AI keys.

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

### 🔗 2. Link the command-line tool wrapper

Make the wrapper script executable and create a symbolic link to it in your bin directory.

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 🚀 3. Run it

Invoke the tool with the 'create' command, followed by the type of issue and a brief description.

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

Below are the various uses and commands you can leverage when using the jira-creator.

### 🆕 Create Issues

Create new issues of various types. Use the `--edit` flag to open the issue in your `$EDITOR`, or use `--dry-run` to print the payload without creating the issue.

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

### 🔁 Change or Migrate Issue Type

Change the type of an existing issue or migrate an issue from one type to another.

```bash
rh-issue change AAP-12345 story
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

Edit the description of an existing issue. By default, AI will be used to enhance the description. If you don't want to use AI, use the `--no-ai` flag.

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🧍 Unassign Issue

Remove the assignee from an issue.

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

List all issues, or filter the list by project, component, and user.

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

Set the priority level of an existing issue.

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

Manage the sprints an issue is assigned to.

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

Set the status of an existing issue.

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

Jira-creator supports plug-in AI providers. Here's how to set up a few of the supported providers.

### ✅ OpenAI

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional
```

### 🖥 GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export INSTRUCTLAB_URL=http://localhost:11434/api/generate
export INSTRUCTLAB_MODEL=instructlab
```

### 🧠 BART

```bash
export AI_PROVIDER=bart
export BART_URL=http://localhost:8000/bart
```

### 🧠 DeepSeek

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
docker compose exec ollama ollama pull deepseek-r1:7b
export AI_PROVIDER=deepseek
export DEEPSEEK_URL=http://localhost:11434/api/generate
```

### 🪫 Noop

The Noop provider does nothing. It's useful if you want to turn off AI enhancements temporarily.

```bash
export AI_PROVIDER=noop
```

---

## 🛠 Dev Setup

Set up the development environment by installing the necessary packages.

```bash
pipenv install --dev
```

### Testing & Linting

Run tests, perform linting checks, and auto-fix formatting issues.

```bash
make test
make lint
make format  # auto-fix formatting
```

---

## ⚙️ How It Works

Jira-creator works by:

- Loading field definitions from `.tmpl` files under `templates/`
- Using the `TemplateLoader` to generate Markdown descriptions
- Optionally applying AI cleanup for readability and structure
- Sending the issue to JIRA via the REST API (or dry-running it if preferred)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).