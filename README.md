# jira-creator 📝

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. Create your config file and enable autocomplete 📂.

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
This sets up your environment variables for the Jira Creator tool. Replace the dummy values with your own data. 

### 2. Link the command-line tool wrapper 🔗.

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```
This creates a symbolic link to conveniently run the tool from any location.

### 3. Run it 🏃‍♀️.

```bash
rh-issue create story "Improve onboarding experience"
```
This command will create a new story issue titled "Improve onboarding experience".

---

## 🧪 Usage & Commands

### 🆕 Create Issues

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```
These commands create issues of various types. The `--edit` flag opens the issue in your default editor for further refinement. The `--dry-run` flag prints the payload without creating the issue, useful for testing.

### 🔁 Change Issue Type

```bash
rh-issue change AAP-12345 story
```
This command changes the type of the issue AAP-12345 to 'story'.

### 🔁 Migrate Issue

```bash
rh-issue migrate AAP-54321 story
```
This command migrates the issue AAP-54321 to the type 'story'.

### ✏️ Edit Description

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```
These commands allow you to edit the description of the issue AAP-98765, with the second command bypassing the AI-enhanced description process.

### 🧍 Unassign Issue

```bash
rh-issue unassign AAP-12345
```
This command unassigns the issue AAP-12345.

### 📋 List Issues

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```
These commands list issues. The second command lists issue specific to a particular project, component, and user.

### 🏷️ Set Priority

```bash
rh-issue set-priority AAP-123 High
```
This command sets the priority of the issue AAP-123 to 'High'.

### 📅 Sprint Management

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```
These commands manage the sprint association of issues.

### 🚦 Set Status

```bash
rh-issue set-status AAP-123 "In Progress"
```
This command sets the status of the issue AAP-123 to 'In Progress'.

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`.

### ✅ OpenAI

```bash
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL=gpt-4  # Optional
```
This sets up OpenAI as your AI provider.

### 🦙 LLama3

```bash
docker compose exec ollama ollama pull LLama3
export AI_PROVIDER=LLama3
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=LLama3
```
This sets up LLama3 as your AI provider.

### 🧠 DeepSeek

```bash
docker compose exec ollama ollama pull deepseek-r1:7b
export AI_PROVIDER=deepseek
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=http://localhost:11434/api/generate
```
This sets up DeepSeek as your AI provider.

### 🖥 GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```
This sets up GPT4All as your AI provider.

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=instructlab
```
This sets up InstructLab as your AI provider.

### 🧠 BART

```bash
export AI_PROVIDER=bart
export AI_URL=http://localhost:8000/bart
```
This sets up BART as your AI provider.

### 🪫 Noop

```bash
export AI_PROVIDER=noop
```
This sets up Noop as your AI provider.

---

## 🛠 Dev Setup

```bash
pipenv install --dev
```
This installs the necessary development dependencies.

### Testing & Linting

```bash
make test
make lint
make format  # autofix formatting
```
These commands run tests, lint code, and auto-fix any formatting issues respectively.

---

## ⚙️ How It Works

Jira Creator works by loading field definitions from `.tmpl` files found in the `templates/` directory. It generates compact and informative issue descriptions using a `TemplateLoader`. Optionally, it applies AI enhancements to cleanup the descriptions for better readability and structure. The cleaned up descriptions are then sent to JIRA via its REST API or just printed as a dry-run.

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE).