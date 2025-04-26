import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import requests

api_key = os.environ.get("AI_API_KEY")
endpoint = "https://api.openai.com/v1/chat/completions"
model = os.environ.get("AI_MODEL")


def extract_code_from_output(output):
    lines = output.splitlines()
    code = None

    for line in lines:
        if line.startswith("```python"):
            code = []
        elif code is not None:
            if line.startswith("```"):
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


def validate_pycompile(file_path: str) -> bool:
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", file_path], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Syntax error in {file_path}: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error validating {file_path}: {str(e)}")
        return False


def harden_file(file_path: str, debug: bool, validate: bool):
    with open(file_path, "r") as f:
        source_code = f.read()

    prompt = f"""
    You are a Python expert focused on improving code quality and enhancing type safety.

    Please review the following Python code, add type hinting where appropriate,
    and ensure that the code is type-hardened to enforce stricter type checking
    and improve overall type safety.

    Respond with the updated code only. Do not include any explanations,
    summaries, or additional comments.

    Here is the code to improve:
    ============================
    {source_code}
    """

    improved_code = improve_text(prompt, source_code)
    improved_code = extract_code_from_output(improved_code)

    # Create a temporary file to hold the improved code
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(improved_code.encode("utf-8"))
        temp_file_path = temp_file.name

    if debug:
        print(f"Improved code written to temporary file: {temp_file_path}")

    if validate and not validate_pycompile(temp_file_path):
        print("Python compilation validation failed. Not moving the file.")
        os.remove(temp_file_path)
        return

    # If validation passed, replace the original file with the improved code
    shutil.move(temp_file_path, file_path)

    if debug:
        print(f"File '{file_path}' has been successfully hardened.")


def process_directory(directory: str, debug: bool, validate: bool, recursive: bool):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if debug:
                    print(f"Processing file: {file_path}")
                harden_file(file_path, debug, validate)

        if not recursive:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Harden Python code using OpenAI API")
    parser.add_argument("path", help="Path to the Python file or directory to harden")
    parser.add_argument(
        "--recursive", action="store_true", help="Recursively process directories"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--validate-pycompile",
        action="store_true",
        help="Validate Python syntax after improvements",
    )
    args = parser.parse_args()

    if os.path.isdir(args.path):
        process_directory(
            args.path, args.debug, args.validate_pycompile, args.recursive
        )
    elif os.path.isfile(args.path):
        harden_file(args.path, args.debug, args.validate_pycompile)
    else:
        print(f"Error: {args.path} is not a valid file or directory.")
        sys.exit(1)
