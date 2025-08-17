# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. Create your config file and enable autocomplete

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
export JIRA_JPAT="your_jira_personal_access_token"
export JIRA_AI_PROVIDER=openai
export JIRA_AI_API_KEY=sk-...
export JIRA_AI_MODEL="gpt-4o-mini"
export JIRA_URL="https://issues.redhat.com"
export JIRA_PROJECT_KEY="AAP"
export JIRA_AFFECTS_VERSION="aa-latest"
export JIRA_COMPONENT_NAME="analytics-hcc-service"
export JIRA_PRIORITY="Normal"
export JIRA_BOARD_ID=21125
export JIRA_EPIC_FIELD="customfield_12311140"
export JIRA_ACCEPTANCE_CRITERIA_FIELD="customfield_12315940"
export JIRA_BLOCKED_FIELD="customfield_12316543"
export JIRA_BLOCKED_REASON_FIELD="customfield_12316544"
export JIRA_STORY_POINTS_FIELD="customfield_12310243"
export JIRA_SPRINT_FIELD="customfield_12310940"
export JIRA_VOSK_MODEL="/home/daoneill/.vosk/vosk-model-small-en-us-0.15"

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

### 2. Link the command-line tool wrapper

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 3. Run it

```bash
rh-issue create story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

## Commands

### add-comment
Add a comment to a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `-t, --text`: Comment text. If not provided, an editor will open for you to enter your comment.
  - `--no-ai`: Skip AI text improvement.

- **Example:**
  ```bash
  jira-cli add-comment PROJ-123 -t "This issue is resolved."
  ```

### add-flag
Add a flag to a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).

- **Example:**
  ```bash
  jira-cli add-flag PROJ-123
  ```

### add-to-sprint
Add an issue to a sprint and optionally assign it.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `sprint_name` (required): The name of the sprint.
  - `-a, --assignee`: Assignee username. Defaults to the current user if not specified.

- **Example:**
  ```bash
  jira-cli add-to-sprint PROJ-123 "Sprint 1" -a username
  ```

### assign
Assign a Jira issue to a user.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `assignee` (required): Username of the person to assign the issue to.

- **Example:**
  ```bash
  jira-cli assign PROJ-123 username
  ```

### block
Mark a Jira issue as blocked.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `reason` (required): The reason for blocking the issue.

- **Example:**
  ```bash
  jira-cli block PROJ-123 "Waiting for approval."
  ```

### blocked
List blocked issues.

- **Arguments:**
  - `--user`: Filter by assignee (username).
  - `--project`: Project key override.
  - `--component`: Component name override.

- **Example:**
  ```bash
  jira-cli blocked --user username
  ```

### change
Change issue type.

- **Arguments:**
  - `issue_key` (required): The Jira issue id/key.
  - `new_type` (required): New issue type.

- **Example:**
  ```bash
  jira-cli change PROJ-123 "Bug"
  ```

### clone-issue
Create a copy of an existing Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key to clone (e.g., `PROJ-123`).
  - `-s, --summary-suffix`: Suffix to add to the cloned issue summary (default: ' (Clone)').

- **Example:**
  ```bash
  jira-cli clone-issue PROJ-123 -s " (Clone)"
  ```

### create-issue
Create a new Jira issue using templates.

- **Arguments:**
  - `type` (required): Type of issue to create.
  - `summary` (required): Issue summary/title.
  - `-e, --edit`: Open editor to modify the description before submission.
  - `--dry-run`: Preview the issue without creating it.
  - `--no-ai`: Skip AI text improvement.

- **Example:**
  ```bash
  jira-cli create-issue "Task" "Implement new feature" --edit
  ```

### edit-issue
Edit a Jira issue description.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `--no-ai`: Skip AI text improvement.
  - `--lint`: Run interactive linting on the description.

- **Example:**
  ```bash
  jira-cli edit-issue PROJ-123 --lint
  ```

### list-issues
List issues from a project with various filters.

- **Arguments:**
  - `-p, --project`: Project key (uses the `JIRA_PROJECT_KEY` env if not specified).
  - `-c, --component`: Filter by component name.
  - `-a, --assignee`: Filter by assignee username.
  - `-r, --reporter`: Filter by reporter username.
  - `-s, --status`: Filter by status.
  - `--summary`: Filter by summary containing text.
  - `--blocked`: Show only blocked issues.
  - `--unblocked`: Show only unblocked issues.
  - `--sort`: Sort by field(s), comma-separated.
  - `-m, --max-results`: Maximum number of results (default: 100).

- **Example:**
  ```bash
  jira-cli list-issues -p "PROJ" --status "Open" --sort "priority"
  ```

### open-issue
Open a Jira issue in your web browser.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).

- **Example:**
  ```bash
  jira-cli open-issue PROJ-123
  ```

### remove-flag
Remove a flag from a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).

- **Example:**
  ```bash
  jira-cli remove-flag PROJ-123
  ```

### search
Search for issues using JQL (Jira Query Language).

- **Arguments:**
  - `jql` (required): JQL query string (e.g., `'project = ABC AND status = Open'`).
  - `-m, --max-results`: Maximum number of results to return (default: 50).

- **Example:**
  ```bash
  jira-cli search "project = ABC AND status = Open" -m 20
  ```

### set-acceptance-criteria
Set the acceptance criteria for a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `acceptance_criteria` (required): The acceptance criteria (can be multiple words).

- **Example:**
  ```bash
  jira-cli set-acceptance-criteria PROJ-123 "Acceptance criteria must be met."
  ```

### set-priority
Set the priority of a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `priority` (required): Priority level to set.

- **Example:**
  ```bash
  jira-cli set-priority PROJ-123 "High"
  ```

### set-status
Set the status of a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `status` (required): The status to transition to.

- **Example:**
  ```bash
  jira-cli set-status PROJ-123 "In Progress"
  ```

### set-summary
Set the summary of a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `summary` (required): The new summary text for the issue.

- **Example:**
  ```bash
  jira-cli set-summary PROJ-123 "Updated issue summary"
  ```

### unassign
Remove the assignee from a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).

- **Example:**
  ```bash
  jira-cli unassign PROJ-123
  ```

### unblock
Remove the blocked status from a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).

- **Example:**
  ```bash
  jira-cli unblock PROJ-123
  ```

### validate-issue
Validate a Jira issue against quality standards.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).
  - `--no-ai`: Skip AI-powered quality checks.
  - `--no-cache`: Skip cache and force fresh validation.

- **Example:**
  ```bash
  jira-cli validate-issue PROJ-123 --no-ai
  ```

### view-issue
View detailed information about a Jira issue.

- **Arguments:**
  - `issue_key` (required): The Jira issue key (e.g., `PROJ-123`).

- **Example:**
  ```bash
  jira-cli view-issue PROJ-123
  ```

### view-user
View detailed information about a Jira user.

- **Arguments:**
  - `account_id` (required): The user's account ID or username.

- **Example:**
  ```bash
  jira-cli view-user username
  ```

### vote-story-points
Vote on story points.

- **Arguments:**
  - `issue_key` (required): The Jira issue id/key.
  - `points` (required): Number of story points to vote.

- **Example:**
  ```bash
  jira-cli vote-story-points PROJ-123 5
  ```

---

## 🤖 AI Provider Support

You can integrate different AI providers by setting the `JIRA_AI_PROVIDER` environment variable.

For model management, you can use Ollama:

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```

### ✅ OpenAI

```bash
export JIRA_AI_PROVIDER=openai
export JIRA_AI_API_KEY=sk-...
export JIRA_AI_MODEL=gpt-4  # Optional
```

### 🦙 LLama3

```bash
docker compose exec ollama ollama pull LLama3
export JIRA_AI_PROVIDER=LLama3
export JIRA_AI_URL=http://localhost:11434/api/generate
export JIRA_AI_MODEL=LLama3
```

### 🧠 DeepSeek

```bash
docker compose exec ollama ollama pull deepseek-r1:7b
export JIRA_AI_PROVIDER=deepseek
export JIRA_AI_URL=http://localhost:11434/api/generate
export JIRA_AI_MODEL=http://localhost:11434/api/generate
```

### 🖥 GPT4All

```bash
pip install gpt4all
export JIRA_AI_PROVIDER=gpt4all
# WIP
```

### 🧪 InstructLab

```bash
export JIRA_AI_PROVIDER=instructlab
export JIRA_AI_URL=http://localhost:11434/api/generate
export JIRA_AI_MODEL=instructlab
# WIP
```

### 🧠 BART

```bash
export JIRA_AI_PROVIDER=bart
export JIRA_AI_URL=http://localhost:8000/bart
# WIP
```

### 🪫 Noop

```bash
export JIRA_AI_PROVIDER=noop
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
make super-lint
```

---

## ⚙️ How It Works

- Loads field definitions from `.tmpl` files located in the `templates/` directory
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for improved readability and structure
- Sends issues to JIRA via REST API (or performs dry runs)

---

## 📜 License

This project is licensed under the [Apache License](./LICENSE)