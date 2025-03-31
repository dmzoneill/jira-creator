# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 🔧 Step 1. Create Your Config File and Enable Autocomplete

Autocomplete enables you to quickly and efficiently use the JIRA command-line tool. Follow the below commands to set up autocomplete:

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

---

### 🔗 Step 2. Link the Command-Line Tool Wrapper

This creates a symbolic link to the command-line tool wrapper, allowing you to use the tool from any location:

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 🏃‍♀️ Step 3. Run It

Here's how to create a story issue:

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

### 🆕 Create Issues

You can use the `create` command to make various kinds of issues:

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

The `--edit` flag opens the issue's description in your `$EDITOR` for editing, and `--dry-run` prints the payload without creating the issue.

### 🔀 Change Issue Type

You can alter the type of an existing issue with the `change` command:

```bash
rh-issue change AAP-12345 story
```

### ➡️ Migrate Issue

The `migrate` command allows you to move an issue to a different type:

```bash
rh-issue migrate AAP-54321 story
```

### ✏️ Edit Description

Use the `edit` command to modify the description of an issue:

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

The `--no-ai` flag lets you edit without AI assistance.

### 🧍 Unassign Issue

The `unassign` command removes the current assignee from an issue:

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

The `list` command shows all issues, with optional filtering:

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

Use the `set-priority` command to change the priority of an issue:

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

The `set-sprint`, `remove-sprint`, and `add-sprint` commands help manage sprints:

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

The `set-status` command changes the status of an issue:

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`. Here are some examples:

- OpenAI:

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional
```

- GPT4All:

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```

- InstructLab:

```bash
export AI_PROVIDER=instructlab
export INSTRUCTLAB_URL=http://localhost:11434/api/generate
export INSTRUCTLAB_MODEL=instructlab
```

- BART:

```bash
export AI_PROVIDER=bart
export BART_URL=http://localhost:8000/bart
```

- DeepSeek:

```bash
export AI_PROVIDER=deepseek
export DEEPSEEK_URL=http://localhost:8000/deepseek
```

- Noop:

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