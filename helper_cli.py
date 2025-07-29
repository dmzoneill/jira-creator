import os
import sys

import requests

api_key = os.environ.get("JIRA_AI_API_KEY")
endpoint = "https://api.openai.com/v1/chat/completions"
model = os.environ.get("JIRA_AI_MODEL")


def extract_code_from_output(output):
    lines = output.splitlines()
    code = None

    for line in lines:
        # Look for file paths starting with '#'
        if line.startswith("```python"):
            # If we're currently processing a file, save its content
            code = []
        elif code is not None:
            # Add lines to the current test content
            if line.startswith("```"):
                # Skip lines containing ```, this is a code block delimiter
                continue
            code.append(line)

    return "\n".join(code)


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
        "temperature": 0.5,
    }

    response = requests.post(endpoint, json=body, headers=headers, timeout=120)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        print(response.content)
        raise Exception("improve text not 200")


# Function to generate unit tests using OpenAI
def generate_code(command_name, user_prompt):
    # Load the source code for the command files
    cli_source_file = f"commands/cli_{command_name}.py"

    # Define the system prompt for generating unit tests, including example tests
    system_prompt = f"""
    You are a helpful assistant that generates code that works
    with the JiraClient interface.

    You are given a function implementation that requires updating.
    Your task is to modify/improve the function based on the source
    code provided and any additional requests.

    The first parameter to the function is `jira`, a reference
    to a object JiraClient that implements {command_name}.

    The 2nd parameter is a args object that contains member attributes required for
    call to the Jiraclient function {command_name}.

    Here is an example:
    ======================================
    def cli_add_sprint(jira, args):
    try:
        jira.add_sprint(args.issue_key, args.sprint_name)
        print(f"✅ Added to sprint '{{args.sprint_name}}'")
        return True
    except AddSprintError as e:
        msg = f"❌ {{e}}"
        print(msg)
        raise AddSprintError(msg)

    Since you are calling a wrapper function on JiraClient.
    You typically just need to provide an issue key and some additional args.

    Wrapper funtion
    ====================
    def add_sprint(self, issue_key, sprint_name):
        return add_sprint(
            self._request, self.board_id, issue_key, sprint_name
        )

    **Return only the updated function. Do not provide any explanations
    or extra information.**

    """

    # Read the source code
    with open("jira_creator/" + cli_source_file, "r") as f:
        o_source = f.read()

    with open("jira_creator/" + f"rest/ops/{command_name}.py", "r") as f:
        rest_o_source = f.read()

    user_prompt = f"""
    {user_prompt}
    Code to update
    ============================
    {o_source}

    Jira cleint {command_name}
    ============================
    {rest_o_source}
    """

    # Call the OpenAI improve_text function to generate the unit tests
    generated_source = improve_text(system_prompt, user_prompt)

    # Extract the test files from the generated output
    source = extract_code_from_output(generated_source)

    with open(
        "jira_creator/" + cli_source_file.format(command_name=command_name), "w"
    ) as f:
        f.write(source)

    print(f"Cli function generated: {command_name}")


# Entry point of the script
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python helper_cli.py <command_name> <prompt>")
        sys.exit(1)

    command_name = sys.argv[1]
    prompt = sys.argv[2]
    generate_code(command_name, prompt)
