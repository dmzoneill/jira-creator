# jira-creator

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)
![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)
![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)

A CLI tool for creating JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## 🚀 Quick Start (Under 30 Seconds)

### 1️⃣ Create a Config File and Enable Autocomplete

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

This block of code creates a new configuration file and sets environment variables for the JIRA Personal Access Token, the AI provider, the OpenAI API key, and other necessary variables. The last command activates autocomplete.

### 2️⃣ Link the CLI Wrapper

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

This command makes the wrapper script executable and creates a symbolic link to it, allowing you to run the script from any location.

### 3️⃣ Run JIRA Creator

```bash
rh-issue create story "Improve onboarding experience"
```

This command creates a new JIRA story with the title "Improve onboarding experience".

---

## 💡 Usage & Commands

### 🆕 Create Issues

Create new issues of various types:

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

Use `--edit` to open your `$EDITOR` for inputting the description, and `--dry-run` to print the payload without creating the issue.

### 🔁 Change Issue Type

Change the type of an existing issue:

```bash
rh-issue change AAP-12345 story
```

### 🔁 Migrate Issue

Migrate an issue to another project:

```bash
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

Edit the description of an issue:

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🧍 Unassign Issue

Unassign yourself from an issue:

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

List all issues or filter them by project, component, or user:

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

Set the priority of an issue:

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

Manage the sprint of an issue:

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

Set the status of an issue:

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`. Here's how to set up a few popular providers:

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
export AI_PROVIDER=deepseek
export DEEPSEEK_URL=http://localhost:8000/deepseek
```

### 🪫 Noop

```bash
export AI_PROVIDER=noop
```

---

## 🛠 Dev Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make format  # auto-fix formatting
```

---

## ⚙️ How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).