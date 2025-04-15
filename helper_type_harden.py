import os
import sys

import requests

api_key = os.environ.get("AI_API_KEY")
endpoint = "https://api.openai.com/v1/chat/completions"
model = os.environ.get("AI_MODEL")


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


def harden_file(file_path: str):
    # Read the source code from the specified file
    with open(file_path, "r") as f:
        source_code = f.read()

    # Define the prompt to instruct OpenAI to harden the Python code
    prompt = f"""
    You are a helpful assistant that improves and hardens Python code.

    Please review the following Python source code and type harden it.

    **respond with the code only**

    Here is the code to improve:
    ============================
    {source_code}
    """

    # Send the source code to OpenAI for improvement
    improved_code = improve_text(prompt, source_code)
    improved_code = extract_code_from_output(improved_code)
    print(improved_code)

    # Write the improved code back to the same file
    with open(file_path, "w") as f:
        f.write(improved_code)

    print(f"File '{file_path}' has been successfully hardened.")


# Entry point of the script
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python harden_code.py <file>")
        sys.exit(1)

    file = sys.argv[1]
    harden_file(file)
