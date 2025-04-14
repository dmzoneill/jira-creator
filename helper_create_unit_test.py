import os
import sys

import requests

# Define the paths for the source files and test files
CLI_TEST_PATH = "tests/commands/test_{command_name}_cli.py"
REST_TEST_PATH = "tests/rest/ops/test_{command_name}.py"

api_key = os.environ.get("AI_API_KEY")
endpoint = "https://api.openai.com/v1/chat/completions"
model = os.environ.get("AI_MODEL")


def extract_tests_from_output(output):
    lines = output.splitlines()

    cli_test_code = []
    rest_test_code = []

    current_test = None
    current_test_content = None

    for line in lines:
        # Look for file paths starting with '#'
        if line.startswith("# tests/"):
            # If we're currently processing a file, save its content
            if current_test:
                # Save the previous test content to the correct file
                if "commands" in str(current_test):
                    cli_test_code = current_test_content
                else:
                    rest_test_code = current_test_content

            # Start a new test file
            current_test = line.strip()
            current_test_content = []

        elif current_test:
            # Add lines to the current test content
            if line.startswith("```"):
                # Skip lines containing ```, this is a code block delimiter
                continue
            current_test_content.append(line)

    # Capture the last file's content after loop ends
    if current_test:
        if "commands" in current_test:
            cli_test_code = current_test_content
        else:
            rest_test_code = current_test_content

    res = "\n".join(cli_test_code), "\n".join(rest_test_code)
    return res


def improve_text(prompt: str, text: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.8,
    }

    response = requests.post(endpoint, json=body, headers=headers, timeout=120)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()

    return ""


# Function to generate unit tests using OpenAI
def generate_unit_tests(command_name):
    # Load the source code for the command files
    jiracli_source_file = "jira_creator/rh_jira.py"
    restclient_source_file = "jira_creator/rest/client.py"
    cli_source_file = f"jira_creator/commands/cli_{command_name}.py"
    rest_source_file = f"jira_creator/rest/ops/{command_name}.py"

    # Read the source code
    with open(cli_source_file, "r") as f:
        cli_source_code = f.read()

    with open(rest_source_file, "r") as f:
        rest_source_code = f.read()

    # Read the source code
    with open(jiracli_source_file, "r") as f:
        jiracli_source_code = f.read()

    with open(restclient_source_file, "r") as f:
        restclient_source_code = f.read()

    # Define the system prompt for generating unit tests, including example tests
    system_prompt = f"""
    You are a helpful assistant that generates unit tests. Below is the source code for a Python command.
    Your task is to generate **only** the unit test code. Do not explain, do not provide extra information.

    You will be provided with the source code for commands.
    JiraClient, JiraCli are provided for context

    Please generate the unit tests for:
    1. **CLI Unit Test**: Create a unit test for the CLI command in the file
       tests/commands/test_{command_name}_cli.py.
    2. **REST Unit Test**: Create a unit test for the REST API command in the file
       tests/rest/ops/test_{command_name}.py.

    JiraClient
    ============================
    {jiracli_source_code}

    JiraCli
    ============================
    {restclient_source_code}

    Example CLI Unit Test:
    ============================
    from unittest.mock import MagicMock
    import pytest
    from exceptions.exceptions import AiError

    def test_add_comment_ai_fail(cli, capsys):
        # Mock the add_comment method
        # cli.jira = MagicMock
        # cli.ai_provider = MagicMock()

        class Args:
            issue_key = "AAP-test_add_comment_ai_fail"
            text = "Comment text"

        cli.add_comment(Args())

        # Capture output and assert
        out = capsys.readout().out
        assert "Success" in out

    ============================

    Example REST Unit Test:
    ============================
    from unittest.mock import MagicMock

    def test_add_comment(client):
        client._request = MagicMock(return_value={{}})

        client.add_comment("AAP-test_add_comment", "This is a comment")

        client._request.assert_called_once_with(
            "POST",
            "/rest/api/2/issue/AAP-test_add_comment/comment",
            json={{"body": "This is a comment"}},
        )
    ============================

    Generate **only** the unit test code.
    """

    user_prompt = f"""
    CLI Source Code:
    {cli_source_code}

    REST Source Code:
    {rest_source_code}
    """

    # Call the OpenAI improve_text function to generate the unit tests
    generated_unit_tests = improve_text(system_prompt, user_prompt)

    if generate_unit_tests == "":
        return

    # Extract the test files from the generated output
    cli_unit_test, rest_unit_test = extract_tests_from_output(generated_unit_tests)

    # Write the unit tests to the respective files
    with open(
        "jira_creator/" + CLI_TEST_PATH.format(command_name=command_name), "w"
    ) as f:
        f.write(cli_unit_test)

    with open(
        "jira_creator/" + REST_TEST_PATH.format(command_name=command_name), "w"
    ) as f:
        f.write(rest_unit_test)

    print(f"Unit tests generated for command: {command_name}")


# Entry point of the script
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_unit_tests.py <command_name>")
        sys.exit(1)

    command_name = sys.argv[1]
    generate_unit_tests(command_name)
