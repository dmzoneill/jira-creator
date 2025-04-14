# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Generate JIRA issues (stories, bugs, epics, spikes, tasks) speedily with standardized templates and optional AI-enhanced descriptions.

## Quick Start (Under 30 Seconds)

### 1. Generate your config file and enable autocomplete.

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
export JIRA_EPIC_FIELD="customfield_12311140"
export JIRA_ACCEPTANCE_CRITERIA_FIELD="customfield_12315940"
export JIRA_BLOCKED_FIELD="customfield_12316543"
export JIRA_BLOCKED_REASON_FIELD="customfield_12316544"
export JIRA_STORY_POINTS_FIELD="customfield_12310243"
export JIRA_SPRINT_FIELD="customfield_12310940"
export VOSK_MODEL="/home/daoneill/.vosk/vosk-model-small-en-us-0.15"

# Activate autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

### 2. Link the command-line tool wrapper

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 3. Execute it

```bash
rh-issue create story "Improve onboarding experience"
```

## Usage & Commands

# Jira CLI Documentation

## ai-helper
The `ai-helper` command is for soliciting assistance from the AI. 

Give a string that describes a sequence of actions, and the AI will support you in executing these actions. To make the AI speak out the response, utilize the `--voice` argument.

### Example:
```
ai-helper prompt "Create a new issue"
ai-helper --voice prompt "Create a new issue"
```

## create-issue
The `create-issue` command creates a new issue in JIRA. 

Specify the issue type (bug, story, epic, task, spike) and the issue title with `type` and `summary` arguments, respectively. Use the `--edit` argument if you want to edit the issue right after creating it. To simulate issue creation without actually creating it, use the `--dry-run` argument.

### Example:
```
create-issue type bug summary "Bug in the login page"
create-issue type story summary "Add a new feature" --edit
create-issue type epic summary "New epic task" --dry-run
```

## edit-issue
The `edit-issue` command edits any existing issue in JIRA.

Give the JIRA issue id/key with the `issue_key` argument. If you want to edit the issue without AI help, use the `--no-ai` argument.

### Example:
```
edit-issue issue_key "BUG-123"
edit-issue issue_key "BUG-123" --no-ai
```

## set-priority
The `set-priority` command changes the priority of any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument and the priority (normal, major, critical) with the `priority` argument.

### Example:
```
set-priority issue_key "BUG-123" priority major
```

## set-story-epic
The `set-story-epic` command links a story to an epic in JIRA. 

Specify the JIRA story id/key and epic id/key using the `issue_key` and `epic_key` arguments, respectively.

### Example:
```
set-story-epic issue_key "STORY-123" epic_key "EPIC-123"
```

## set-status
The `set-status` command changes the status of any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument and the status (Closed, In Progress, Refinement, New) with the `status` argument.

### Example:
```
set-status issue_key "BUG-123" status In Progress
```

## change
The `change` command changes the type of any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument and the new type (bug, story, epic, task, spike) with the `new_type` argument.

### Example:
```
change issue_key "TASK-123" new_type bug
```

## migrate
The `migrate` command transfers any existing issue in JIRA to a different type.

Provide the JIRA issue id/key with the `issue_key` argument and the new type (bug, story, epic, task, spike) with the `new_type` argument.

### Example:
```
migrate issue_key "TASK-123" new_type bug
```

## assign
The `assign` command allocates any existing issue in JIRA to a user.

Provide the JIRA issue id/key with the `issue_key` argument and the assignee with the `assignee` argument.

### Example:
```
assign issue_key "BUG-123" assignee "John Doe"
```

## unassign
The `unassign` command removes an existing issue in JIRA from a user.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
unassign issue_key "BUG-123"
```

## block
The `block` command halts any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument and the reason for blocking the issue with the `reason` argument.

### Example:
```
block issue_key "BUG-123" reason "Dependency on another task"
```

## unblock
The `unblock` command unblocks any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
unblock issue_key "BUG-123"
```

## vote-story-points
The `vote-story-points` command votes for the story points of any existing story in JIRA.

Specify the JIRA issue id/key with the `issue_key` argument and the story point estimate (integer) with the `points` argument.

### Example:
```
vote-story-points issue_key "STORY-123" points 5
```

## set-story-points
The `set-story-points` command sets the story points of any existing story in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument and the story point estimate (integer) with the `points` argument.

### Example:
```
set-story-points issue_key "STORY-123" points 8
```

## add-sprint
The `add-sprint` command adds any existing issue in JIRA to a sprint.

Provide the JIRA issue id/key with the `issue_key` argument and the name of the sprint with the `sprint_name` argument.

### Example:
```
add-sprint issue_key "BUG-123" sprint_name "Sprint 3"
```

## remove-sprint
The `remove-sprint` command removes any existing issue in JIRA from a sprint.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
remove-sprint issue_key "BUG-123"
```

## add-comment
The `add-comment` command adds a comment to any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
add-comment issue_key "BUG-123"
```

## search
The `search` command searches for issues in JIRA using a JIRA Query Language (JQL) expression.

Give the JQL expression with the `jql` argument.

### Example:
```
search jql "project = 'My Project' AND status = 'In Progress'"
```

## list-issues
The `list-issues` command fetches a list of issues in JIRA.

The issues can be filtered by project, component, assignee, status, summary, reporter using `--project`, `--component`, `--assignee`, `--status`, `--summary`, `--reporter` arguments respectively.

### Example:
```
list-issues --project "My Project" --assignee "John Doe" --status "In Progress"
```

## lint
The `lint` command checks the quality of any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
lint issue_key "BUG-123"
```

## lint-all
The `lint-all` command checks the quality of all the issues in JIRA.

Issues can be filtered by project, component, assignee, reporter using `--project`, `--component`, `--assignee`, `--reporter` arguments respectively.

### Example:
```
lint-all --project "My Project" --assignee "John Doe"
```

## open-issue
The `open-issue` command opens any existing issue in JIRA in your default web browser.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
open-issue issue_key "BUG-123"
```

## view-issue
The `view-issue` command views the details of any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
view-issue issue_key "BUG-123"
```

## view-user
The `view-user` command views the details of a user in JIRA.

Provide the JIRA account ID with the `account_id` argument.

### Example:
```
view-user account_id "123456"
```

## search-users
The `search-users` command searches for users in JIRA.

Provide the search term with the `query` argument.

### Example:
```
search-users query "John"
```

## blocked
The `blocked` command fetches a list of issues in JIRA that are blocked.

Issues can be filtered by user, project, component using `--user`, `--project`, `--component` arguments respectively.

### Example:
```
blocked --user "John Doe" --project "My Project"
```

## talk
The `talk` command makes the AI speak out the response.

Use the `--voice` argument to enable this feature.

### Example:
```
talk --voice
```

## add-flag
The `add-flag` command adds a flag to any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
add-flag issue_key "BUG-123"
```

## remove-flag
The `remove-flag` command removes a flag from any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
remove-flag issue_key "BUG-123"
```

## set-summary
The `set-summary` command sets the summary of any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument and the summary with the `summary` argument.

### Example:
```
set-summary issue_key "BUG-123" summary "New bug in the login page"
```

## clone-issue
The `clone-issue` command clones any existing issue in JIRA.

Provide the JIRA issue id/key with the `issue_key` argument.

### Example:
```
clone-issue issue_key "BUG-123"
```

## AI Provider Support

You can plug in various AI providers by setting `AI_PROVIDER`.

Ollama can be used for managing different models

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

### OpenAI

```bash
export AI_PROVIDER=openai
export AI_API_KEY=sk-...
export AI_MODEL=gpt-4  # Optional
```

### LLama3

```bash
docker compose exec ollama ollama pull LLama3
export AI_PROVIDER=LLama3
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=LLama3
```

### DeepSeek

```bash
docker compose exec ollama ollama pull deepseek-r1:7b
export AI_PROVIDER=deepseek
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=http://localhost:11434/api/generate
```

### GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
# WIP
```

### InstructLab

```bash
export AI_PROVIDER=instructlab
export AI_URL=http://localhost:11434/api/generate
export AI_MODEL=instructlab
# WIP
```

### BART

```bash
export AI_PROVIDER=bart
export AI_URL=http://localhost:8000/bart
# WIP
```

### Noop

```bash
export AI_PROVIDER=noop
```

## Dev Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make super-lint
```

## How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to create Markdown descriptions
- Optionally applies AI cleanup for improved readability and structure
- Sends to JIRA via REST API (or dry-runs it)

## License

This project is licensed under the [Apache License](./LICENSE).