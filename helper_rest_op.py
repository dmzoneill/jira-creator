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
        raise Exception("improve text not 200")


# Function to generate unit tests using OpenAI
def generate_code(command_name, user_prompt):
    # Load the source code for the command files
    rest_source_file = f"rest/ops/{command_name}.py"

    # Define the system prompt for generating unit tests, including example tests
    system_prompt = """
    You are a helpful assistant that generates code that works
    with the Jira REST interface (mainly v2).

    You are given a function implementation that requires updating.
    Your task is to modify/improve the function based on the source
    code provided and any additional requests.

    The first parameter to the function is `request_fn`, a reference
    to a function that handles HTTP requests. It has the following signature:

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:

    You should use `request_fn` to make the HTTP request. The path and payload
    may be provided by the user. If so, you **must** use them in your code.
    If not provided, use the default API paths or payloads (e.g., `/rest/api/2/...`).

    **Return only the updated function. Do not provide any explanations
    or extra information.**

    If parameters need to be added, do so as necessary, but maintain the original
    structure of the function unless otherwise specified.

    If the user provides the path, **always use that path** in your code.
    If no path is provided, use the default or fallback path.

    **only** the source code. Do not explain, do not provide extra information.

    """

    # Read the source code
    with open("jira_creator/" + rest_source_file, "r") as f:
        o_source = f.read()

    user_prompt = f"""
    {user_prompt}
    Code
    ============================
    {o_source}
    """

    # Call the OpenAI improve_text function to generate the unit tests
    generated_source = improve_text(system_prompt, user_prompt)

    # Extract the test files from the generated output
    source = extract_code_from_output(generated_source)

    with open(
        "jira_creator/" + rest_source_file.format(command_name=command_name), "w"
    ) as f:
        f.write(source)

    print(f"Rest function generated: {command_name}")


# Entry point of the script
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python helper_rest_op.py <command_name> <prompt>")
        sys.exit(1)

    command_name = sys.argv[1]
    prompt = sys.argv[2]
    generate_code(command_name, prompt)
