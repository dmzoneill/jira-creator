# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## 🚀 Quick Start (Under 30 Seconds)

### 1. 📝 Create your config file and enable autocomplete

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
This will set up your environment variables for the tool. Be sure to replace the placeholder text with your actual credentials and desired settings.

---

### 2. 🔗 Link the command-line tool wrapper

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```
This will make the `rh-issue` command globally accessible from the terminal.

---

### 3. 🏃 Run it

```bash
rh-issue create story "Improve onboarding experience"
```
This will create a new user story with the title "Improve onboarding experience".

---

## 📚 Usage & Commands

### 1️⃣ Create Issues

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```
You can create issues of various types (bug, story, epic, spike) with specific titles. Use `--edit` to open the issue in your default `$EDITOR` for further customization. Use `--dry-run` to generate the issue payload without actually creating it.

### 2️⃣ Change Issue Type

```bash
rh-issue change AAP-12345 story
```
Change the issue type of an existing issue. This command will change the issue with ID AAP-12345 to a "story".

### 3️⃣ Migrate Issue

```bash
rh-issue migrate AAP-54321 story
```
This moves an issue from its current location to another project or issue type. This command will migrate the issue with ID AAP-54321 to a "story".

### 4️⃣ Edit Description

```bash
rh-issue edit AAP-98765
rh-issue edit AAP-98765 --no-ai
```
Edit the description of an existing issue. Use `--no-ai` to edit without the aid of AI.

### 5️⃣ Unassign Issue

```bash
rh-issue unassign AAP-12345
```
Remove any current assignees from an issue.

### 6️⃣ List Issues

```bash
rh-issue list
rh-issue list --project AAP --component api --user jdoe
```
List all issues or filter by project, component, or user.

### 7️⃣ Set Priority

```bash
rh-issue set-priority AAP-123 High
```
Update the priority of an issue. For instance, set the priority of issue AAP-123 to "High".

### 8️⃣ Sprint Management

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```
Manage the sprints associated with an issue. You can add, set, or remove a sprint.

### 9️⃣ Set Status

```bash
rh-issue set-status AAP-123 "In Progress"
```
Change the status of an issue. For instance, set the status of AAP-123 to "In Progress".

---

## 🧠 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`.

We can use ollama for the management for differnet models

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```
Check the below guide to setup your preferred AI Provider.

---

## 🛠️ Dev Setup

```bash
pipenv install --dev
```
This will install all the necessary dependencies for development.

### Testing & Linting

```bash
make test
make lint
make format  # autofix formatting
```
These commands will help in testing, linting, and auto-formatting the code.

---

## 📖 How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

---

## 🗞️ License

This project is licensed under the [Apache License](./LICENSE).