# jira-creator
[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) swiftly using standardized templates and optional AI-enhanced descriptions.

## 💾 Installation and Setup
This section explains how to install and set up the jira-creator on your local system.

### 1. Create your config file and enable autocomplete.
This sets up the environment variables required by the tool, including your JIRA personal access token, AI provider, project key, JIRA server URL, etc.

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

### 2. Link the command-line tool wrapper
This makes the jira-creator tool executable and links it to your system path for easy access.

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 3. Run it
You can now create a Jira issue from the command line.

```bash
rh-issue create story "Improve onboarding experience"
```

## 🏹 Usage & Commands
This section details the various commands and their usage.

### 📝 Create Issues
You can create different types of issues like bugs, stories, epics, spikes, and tasks.

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

The `--edit` flag opens your `$EDITOR` for manual editing of the issue, while the `--dry-run` flag prints the issue payload without actually creating the issue.

### 🔄 Change Issue Type
You can change the type of an existing Jira issue.

```bash
rh-issue change AAP-12345 story
```

### ✈️ Migrate Issue
You can migrate an issue from one type to another.

```bash
rh-issue migrate AAP-54321 story
```

### ✍ Edit Description
You can edit the description of an issue. If you wish to edit without AI enhancement, use the `--no-ai` flag.

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```

### 🚫 Unassign Issue
You can unassign an issue from the current assignee.

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues
You can list all issues or filter by project, component, or user.

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```

### 📌 Set Priority
You can set the priority of an issue.

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management
You can add, remove, or set sprint for an issue.

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status
You can set the status of an issue.

```bash
rh-issue set-status AAP-123 "In Progress"
```

## 🧠 AI Provider Support 
This section describes how to configure different AI providers for enhancing issue descriptions. The AI provider can be specified by setting the `AI_PROVIDER` environment variable.

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```
### ✅ OpenAI
Here's how to configure OpenAI as the AI provider.

```bash
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL=gpt-4  # Optional
```

...and so on for the other AI providers.

## 🛠 Dev Setup
Developers can use the following command to install the tool along with its development dependencies.

```bash
pipenv install --dev
```

### Testing & Linting
You can run tests and lint the code using the following commands.

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