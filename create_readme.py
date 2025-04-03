import ast
import os

import requests


class OpenAIProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in environment.")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

    def improve_text(self, prompt: str, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.8,
        }

        response = requests.post(self.endpoint, json=body, headers=headers, timeout=120)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        raise Exception(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )


def extract_argparse_commands(cli_script):
    """Extract argparse commands and their arguments from a CLI script."""
    with open(cli_script, "r") as f:
        content = f.read()

    # We need to extract both the command and the arguments
    commands = []
    tree = ast.parse(content)

    # Walk through the parsed script to find argparse usage
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", "") == "add_argument"
        ):
            # Extract command and arguments
            command = None
            args = []
            for keyword in node.keywords:
                if keyword.arg == "name":
                    command = keyword.value.s
                elif keyword.arg == "help":
                    args.append(f"  - **help**: {keyword.value.s}")
                elif keyword.arg == "type":
                    args.append(
                        f"  - **type**: {keyword.value.id if isinstance(keyword.value, ast.Name) else keyword.value.s}"
                    )
                elif keyword.arg == "default":
                    args.append(
                        f"  - **default**: {keyword.value.n if isinstance(keyword.value, ast.Constant) else keyword.value.s}"
                    )
            if command:
                commands.append(f"**{command}**: \n" + "\n".join(args))
    return commands


def generate_readme(cli_script, output_readme):
    """Generate the README.md file using OpenAI API."""
    # Step 1: Extract commands and arguments from CLI script
    commands = extract_argparse_commands(cli_script)

    # Template format for the README structure

    # Prepare the final prompt to pass to OpenAI
    prompt = f"""
    You are a helpful assistant that helps generate detailed documentation.

    Here is a template for the README of a command-line tool:

    # jira-creator

    [![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
    ![Python](https://img.shields.io/badge/python-3.8%2B-blue)
    [![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
    [![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

    Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

    ---

    ## ⚡ Quick Start (Under 30 Seconds)

    ### 1. Create your config file and enable autocomplete

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

    ---

    ### 2. Link the command-line tool wrapper

    ```bash
    chmod +x jira_creator/rh-issue-wrapper.sh
    sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
    ```

    ---

    ### 3. Run it

    ```bash
    rh-issue create story "Improve onboarding experience"
    ```

    ---

    ## 🧪 Usage & Commands

    ### 🆕 Create Issues

    ```bash
    rh-issue create bug "Fix login crash"
    rh-issue create story "Refactor onboarding flow"
    rh-issue create epic "Unify frontend UI" --edit
    rh-issue create spike "Evaluate GraphQL support" --dry-run
    ```

    Use `--edit` to use your `$EDITOR`, and `--dry-run` to print the payload without creating the issue.

    ### 🔁 Change Issue Type

    ```bash
    rh-issue change AAP-12345 story
    ```

    ### 🔁 Migrate Issue

    ```bash
    rh-issue migrate AAP-54321 story
    ```

    ### ✏️ Edit Description

    ```bash
    rh-issue edit AAP-98765
    rh-issue edit AAP-98765 --no-ai
    ```

    ### 🧍 Unassign Issue

    ```bash
    rh-issue unassign AAP-12345
    ```

    ### 📋 List Issues

    ```bash
    rh-issue list
    rh-issue list --project AAP --component api --user jdoe
    ```

    ### 🏷️ Set Priority

    ```bash
    rh-issue set-priority AAP-123 High
    ```

    ### 📅 Sprint Management

    ```bash
    rh-issue set-sprint AAP-456 1234
    rh-issue remove-sprint AAP-456
    rh-issue add-sprint AAP-456 "Sprint 33"
    ```

    ### 🚦 Set Status

    ```bash
    rh-issue set-status AAP-123 "In Progress"
    ```

    ---

    ## 🤖 AI Provider Support

    You can plug in different AI providers by setting `AI_PROVIDER`.

    We can use ollama for the management for differnet models

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
    docker compose exec ollama ollama pull LLama3
    export AI_PROVIDER=LLama3
    export AI_URL=http://localhost:11434/api/generate
    export AI_MODEL=LLama3
    ```

    ### 🧠 DeepSeek

    ```bash
    docker compose exec ollama ollama pull deepseek-r1:7b
    export AI_PROVIDER=deepseek
    export AI_URL=http://localhost:11434/api/generate
    export AI_MODEL=http://localhost:11434/api/generate
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

    Now, update this template to include detailed sections for the following commands. Keep the structure and improve the details where possible:

    {commands}

    Be sure to provide:
    - Descriptions for each command and argument.
    - Examples of how to use the commands.
    - Any relevant explanations to improve understanding of the tool.
    - Add icons next to headers for look and feel
    - Provide fully detailed commands and argument and examples
    - Provide AI setup and usage

    """

    # Step 3: Initialize OpenAIProvider
    openai_provider = OpenAIProvider()

    # Step 4: Improve the README content using OpenAI
    readme_content = openai_provider.improve_text(
        "Update and improve this README template with the provided commands.", prompt
    )

    # Step 5: Write the new README content to the output file
    with open(output_readme, "w") as f:
        f.write(readme_content)

    print(f"README updated and saved to {output_readme}")


if __name__ == "__main__":
    # Example usage
    cli_script_path = "jira_creator/rh_jira.py"
    output_readme_path = "README.md"
    generate_readme(cli_script_path, output_readme_path)
