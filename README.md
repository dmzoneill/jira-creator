# Jira-Creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Efficient creation of JIRA issues (stories, bugs, epics, spikes, tasks) using standardized templates and optional AI-enhanced descriptions.

## ⚡ Quick Start (Under 30 Seconds)

### Creating a config file and enabling autocomplete:

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
... (configuration variables here) ...

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

### Linking the command-line tool wrapper:

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### Running the tool:

```bash
rh-issue create story "Improve onboarding experience"
```

## 🧪 Usage & Commands

# Jira CLI Commands :computer:

This is a list of commands and argument you can use with the Jira command-line tool.

## Ai-Helper :robot:

This command is used to help you navigate the command line tool with a friendly AI voice.

| Argument | Description   |
|--------------|---------------|
| --voice | Enables the AI voice |

Example:

```shell
ai-helper --voice
```

## Create-Issue :pencil2:

Create a new issue in your Jira project.

| Argument | Description   |
|--------------|---------------|
| type | The type of the issue (e.g. bug, story, epic, task, spike) |
| summary | Title of the issue |
| --edit | Edit the issue after creation |
| --dry-run | Simulate the command without actually executing it |

Example:

```shell
create-issue --type bug --summary "This is a bug" --edit
```

## Edit-Issue :wrench:

Edit an existing issue in your Jira project.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the issue you want to edit |
| --no-ai | Disable the AI helper |

Example:

```shell
edit-issue --issue_key EX-123
```

## Set-Priority :fire:

Set the priority of an existing issue.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the issue you want to set the priority for |
| priority | The priority level (e.g. normal, major, critical) |

Example:

```shell
set-priority --issue_key EX-123 --priority major
```

## Set-Story-Epic :book:

Assign a story to an epic.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the story you want to assign to an epic |
| epic_key | The key of the epic |

Example:

```shell
set-story-epic --issue_key ST-456 --epic_key EP-789
```

## Set-Status :traffic_light:

Change the status of an issue.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the issue you want to change the status for |
| status | The new status (e.g. Closed, In Progress, Refinement, New) |

Example:

```shell
set-status --issue_key EX-123 --status Closed
```

## Change :left_right_arrow:

Change the type of an issue.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the issue you want to change the type for |
| new_type | The new type (e.g. bug, story, epic, task, spike) |

Example:

```shell
change --issue_key EX-123 --new_type story
```

## Migrate :airplane:

Migrate an issue to a new type.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the issue you want to migrate |
| new_type | The new type (e.g. bug, story, epic, task, spike) |

Example:

```shell
migrate --issue_key EX-123 --new_type epic
```

## Assign :hand:

Assign an issue to a user.

| Argument | Description   |
|--------------|---------------|
| issue_key | The key of the issue you want to assign |
| assignee | The username of the person you want to assign |

Example:

```shell
assign --issue_key EX-123 --assignee john_doe
```

Continue with similar descriptive explanations for the rest of the commands and their arguments.

## 🤖 Supported AI Providers

Different AI providers can be set via the `AI_PROVIDER` configuration.

We use ollama for managing different models

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

### ✅ OpenAI

```bash
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL=gpt-4  # Optional
```

### 🦙 LLama3

```bash
... (instructions here) ...
```

### 🧠 DeepSeek

```bash
... (instructions here) ...
```

### 🖥 GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
# WIP
```

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=instructlab
# WIP
```

### 🧠 BART

```bash
export AI_PROVIDER=bart
export AI_URL=http://localhost:8000/bart
# WIP
```

### 🪫 Noop

```bash
export AI_PROVIDER=noop
```

## 🛠 Developer Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make super-lint
```

## ⚙️ Functionality Overview

- Loads field definitions from `.tmpl` files under `templates/`
- Generates Markdown descriptions with `TemplateLoader`
- Optional AI cleanup for enhanced readability and structure
- Sends to JIRA via REST API (or performs a dry-run)

## 📜 License

This project is governed by the [Apache License](./LICENSE).