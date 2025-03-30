# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 🔧 1. Create your config file and enable autocomplete

Create a configuration file with your JIRA account and project details. This will include your personal access token, AI provider, API keys, JIRA URL, Project Key, Version, Component Name, Priority, and Board ID.

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

### 🔗 2. Link the CLI wrapper

Make the wrapper script executable and link it to your local bin directory. This will allow you to run the CLI tool from anywhere in your terminal.

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 🏃 3. Run it

Create your first JIRA issue with the `rh-issue create` command. 

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

All commands should be initiated with the `rh-issue` prefix.

### 🆕 Create Issues

Create JIRA issues directly from your terminal. Replace "Issue Type" with either "story", "bug", "epic", or "spike". Use `--edit` to open your default terminal text editor for longer descriptions, and `--dry-run` to print out the payload without creating the issue.

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

### 🔁 Change Issue Type

Change the type of an existing issue. Replace "Issue ID" with the ID of the issue you want to change, and "New Type" with the new issue type.

```bash
rh-issue change AAP-12345 story
```

### 🔀 Migrate Issue

Migrate an issue from one project to another. Replace "Issue ID" with the ID of the issue you want to migrate, and "New Project" with the key of the project you want to migrate the issue to.

```bash
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

Edit the description of an existing issue. Replace "Issue ID" with the ID of the issue you want to edit. Use `--no-ai` to disable AI enhancements when editing the description.

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🧍 Unassign Issue

Unassign an issue from a user. Replace "Issue ID" with the ID of the issue you want to unassign.

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

List all issues in a project. Use `--project` to specify a project by its key, `--component` to filter by component, and `--user` to filter by assigned user.

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

Set the priority of an issue. Replace "Issue ID" with the ID of the issue you want to set the priority for, and "Priority" with the desired priority level.

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

Manage sprint assignments for issues. Replace "Issue ID" with the ID of the issue you want to manage, and "Sprint ID" with the ID of the sprint you want to assign or unassign.

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

Set the status of an issue. Replace "Issue ID" with the ID of the issue you want to set the status for, and "Status" with the desired status.

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`. Each AI provider may require additional configuration.

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

- jira-creator loads field definitions from `.tmpl` files located under the `templates/` directory.
- It uses `TemplateLoader` to generate Markdown descriptions.
- Optionally, it applies AI cleanup to enhance the readability and structure of the descriptions.
- It sends the issue to JIRA via the REST API (or prints the payload for a dry-run).

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).