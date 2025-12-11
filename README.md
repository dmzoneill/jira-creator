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
export JIRA_ACCEPTANCE_CRITERIA_FIELD="customfield_12315940"
export JIRA_AFFECTS_VERSION=""

export JIRA_AI_API_KEY="..................."

export JIRA_AI_MODEL="claude-sonnet-4-5@20250929"
export JIRA_AI_PROVIDER="vertex"
export JIRA_AI_URL="http://dontcare/"
export JIRA_BLOCKED_FIELD="customfield_12316543"
export JIRA_BLOCKED_REASON_FIELD="customfield_12316544"
export JIRA_BOARD_ID="21125"
export JIRA_COMPONENT_NAME="analytics-hcc-service"
export JIRA_EPIC_FIELD="customfield_12311140"

export JIRA_JPAT=" .......................... "

export JIRA_PRIORITY="Normal"
export JIRA_PROJECT_KEY="AAP"
export JIRA_SPRINT_FIELD="customfield_12310940"
export JIRA_STORY_POINTS_FIELD="customfield_12310243"
export JIRA_URL="https://issues.redhat.com"
export JIRA_VIEW_COLUMNS="key,issuetype,status,priority,summary,assignee,reporter,sprint,JIRA_STORY_POINTS_FIELD,JIRA_BLOCKED_FIELD"
export JIRA_VOSK_MODEL="~/.vosk/vosk-model-small-en-us-0.15"
export JIRA_WORKSTREAM="44650"
export JIRA_WORKSTREAM_FIELD="customfield_12319275"

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

For a complete list of all available commands with examples, run:

```bash
rh-issue --help
```

Example output:

```
     _ ___ ____      _      ____ ____  _____    _  _____ ___  ____
    | |_ _|  _ \    / \    / ___|  _ \| ____|  / \|_   _/ _ \|  _ \
 _  | || || |_) |  / _ \  | |   | |_) |  _|   / _ \ | || | | | |_) |
| |_| || ||  _ <  / ___ \ | |___|  _ <| |___ / ___ \| || |_| |  _ <
 \___/|___|_| \_\/_/   \_\ \____|_| \_\_____/_/   \_\_| \___/|_| \_\

                   AI-Powered Issue Management 🚀


DESCRIPTION
  A powerful CLI tool for managing JIRA issues with AI-powered
  quality checks, automated fixes, and streamlined workflows.

USAGE
  rh-issue <command> [options]

COMMANDS

  📝 Issue Creation & Management
    batch-create                   Create multiple Jira issues from a directory of input files
      $ rh-issue batch-create /path/to/issues/
      $ rh-issue batch-create ./issue-templates/ --dry-run

    clone-issue                    Create a copy of an existing Jira issue
      $ rh-issue clone-issue AAP-12345
      $ rh-issue clone-issue AAP-12345 --new-summary "Cloned issue"

    create-issue                   Create a new Jira issue using templates
      $ rh-issue create-issue bug 'Login page crashes on submit'
      $ rh-issue create-issue story 'Add password reset feature' --story-points 5
      $ rh-issue create-issue task 'Update documentation' --edit

    edit-issue                     Edit a Jira issue description
      $ rh-issue edit-issue AAP-12345

    update-description             Update the description of a Jira issue from file or stdin
      $ rh-issue update-description AAP-12345 description.md
      $ rh-issue cat description.txt | update-description AAP-12345 -

  🔍 Search & View
    list-blocked                   List all blocked issues with blocker details
      $ rh-issue list-blocked
      $ rh-issue list-blocked --project AAP

    list-issues                    List issues from a project with various filters
      $ rh-issue list-issues AAP
      $ rh-issue list-issues AAP --status "In Progress" --assignee jsmith

    search                         Search for issues using JQL (Jira Query Language)
      $ rh-issue search "project = AAP AND status = Open"
      $ rh-issue search "assignee = currentUser()"

    search-users                   Search for Jira users by name or email
      $ rh-issue search-users "John Smith"
      $ rh-issue search-users jsmith@example.com

    view-issue                     View detailed information about a Jira issue
      $ rh-issue view-issue AAP-12345
      $ rh-issue view-issue AAP-12345 --output json

    view-user                      View detailed information about a Jira user
      $ rh-issue view-user jsmith

  ✏️  Issue Modification
    assign                         Assign a Jira issue to a user
      $ rh-issue assign AAP-12345 jsmith

    change                         Change issue type
      $ rh-issue change AAP-12345

    change-type                    Change the type of a Jira issue
      $ rh-issue change-type AAP-12345 story
      $ rh-issue change-type AAP-12345 bug

    set-acceptance-criteria        Set the acceptance criteria for a Jira issue
      $ rh-issue set-acceptance-criteria AAP-12345 "User can login successfully"

    set-component                  Set the component of a Jira issue
      $ rh-issue set-component AAP-12345 'API Gateway'

    set-priority                   Set the priority of a Jira issue

    set-project                    Set the project of a Jira issue
      $ rh-issue set-project AAP-12345 NEWPROJ

    set-status                     Set the status of a Jira issue
      $ rh-issue set-status AAP-12345 "In Progress"
      $ rh-issue set-status AAP-12345 Done

    set-story-epic                 Link a story to an epic
      $ rh-issue set-story-epic AAP-12345 AAP-100

    set-story-points               Set the story points of a Jira issue
      $ rh-issue set-story-points AAP-12345 5

    set-summary                    Set the summary of a Jira issue
      $ rh-issue set-summary AAP-12345 'Updated issue summary'

    set-workstream                 Set the workstream of a Jira issue
      $ rh-issue set-workstream AAP-12345 Authentication

    unassign                       Remove the assignee from a Jira issue
      $ rh-issue unassign AAP-12345

  🎯 Sprint Management
    add-to-sprint                  Add an issue to a sprint and optionally assign it
      $ rh-issue add-to-sprint AAP-12345 123

    get-sprint                     Get the current active sprint
      $ rh-issue get-sprint 123

    list-sprints                   List all sprints for a board
      $ rh-issue list-sprints 123

    remove-sprint                  Remove an issue from its current sprint
      $ rh-issue remove-sprint AAP-12345

  🔗 Issue Relationships
    add-flag                       Add a flag to a Jira issue
      $ rh-issue add-flag AAP-12345

    add-link                       Create an issue link between two Jira issues
      $ rh-issue add-link AAP-12345 AAP-12346 blocks
      $ rh-issue add-link AAP-12345 AAP-12347 relates-to

    remove-flag                    Remove a flag from a Jira issue
      $ rh-issue remove-flag AAP-12345

  🚧 Blocking & Issues
    block                          Mark a Jira issue as blocked
      $ rh-issue block AAP-12345 AAP-12346
      $ rh-issue block AAP-12345 AAP-12346 "Waiting for API changes"

    blocked                        List blocked issues
      $ rh-issue blocked

    unblock                        Remove the blocked status from a Jira issue
      $ rh-issue unblock AAP-12345 AAP-12346

  ✅ Quality & Validation
    lint                           Lint a single Jira issue for quality and completeness
      $ rh-issue lint AAP-12345
      $ rh-issue lint AAP-12345 --fix

    lint-all                       Lint multiple Jira issues for quality and completeness
      $ rh-issue lint-all --project AAP
      $ rh-issue lint-all --project AAP --ai-fix

    validate-issue                 Validate a Jira issue against quality standards
      $ rh-issue validate-issue AAP-12345

    vote-story-points              Vote on story points
      $ rh-issue vote-story-points AAP-12345 5

  📊 Reporting
    quarterly-connection           Perform a quarterly connection report
      $ rh-issue quarterly-connection --quarter Q1

  🛠️  Utilities
    add-comment                    Add a comment to a Jira issue
      $ rh-issue add-comment AAP-12345 "Adding a status update"

    ai-helper                      Use natural language to interact with Jira
      $ rh-issue ai-helper "Add issue AAP-12345 to the current sprint"
      $ rh-issue ai-helper "Set AAP-12345 to in progress and assign it to me"
      $ rh-issue ai-helper "Create a bug for login page crash" --voice

    config                         Manage configuration profiles for common settings
      $ rh-issue config
      $ rh-issue config --show-all

    migrate                        Migrate issue to a new type
      $ rh-issue migrate AAP-12345 NEWPROJ

    open-issue                     Open a Jira issue in your web browser
      $ rh-issue open-issue AAP-12345

    talk                           Use voice commands to interact with Jira (requires microp...
      $ rh-issue talk
      $ rh-issue talk --voice

OPTIONS
  -h, --help              Show this help message and exit

───────────────────────────────────────────────────────────────────────────────
For more information, visit: https://github.com/dmzoneill/jira-creator
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

## 🔌 Plugin Development

jira-creator uses a plugin architecture. Each command is implemented as a plugin that inherits from `JiraPlugin`.

### Required Plugin Structure

```python
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.plugin_base import JiraPlugin


class AddFlagPlugin(JiraPlugin):
    """Plugin for adding flags to Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the CLI command name (e.g., 'add-flag')."""
        return "add-flag"

    @property
    def category(self) -> str:
        """Return the help category. Defaults to 'Other' if not specified."""
        return "Issue Relationships"

    @property
    def help_text(self) -> str:
        """Return brief help text for the command."""
        return "Add a flag to a Jira issue"

    @property
    def example_commands(self) -> List[str]:
        """Return example command invocations (optional)."""
        return ["add-flag AAP-12345"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the command.

        Args:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        self.rest_operation(client, issue_key=args.issue_key)
        print(f"✅ Flag added to {args.issue_key}")
        return True

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation.

        Args:
            client: JiraClient instance
            **kwargs: Operation-specific parameters

        Returns:
            Dict containing the API response
        """
        return client.ops.add_flag(**kwargs)
```

### Available Categories

Plugins can specify one of these categories for help organization:
- `Issue Creation & Management` - Creating and cloning issues
- `Search & View` - Searching and viewing issues/users
- `Issue Modification` - Updating issue fields
- `Sprint Management` - Sprint-related operations
- `Issue Relationships` - Links, flags, and relationships
- `Blocking & Issues` - Blocking status management
- `Quality & Validation` - Linting and validation
- `Reporting` - Reports and analytics
- `Utilities` - Helper commands
- `Other` - Default for uncategorized plugins

Plugins without a `category` property default to "Other".

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