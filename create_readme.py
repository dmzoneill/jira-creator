import ast
import os

import requests


# /* jscpd:ignore-start */
class OpenAIProvider:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("AI_API_KEY not set in environment.")
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
                    str = (
                        keyword.value.n
                        if isinstance(keyword.value, ast.Constant)
                        else keyword.value.s
                    )
                    args.append(f"  - **default**: {str}")
            if command:
                commands.append(f"**{command}**: \n" + "\n".join(args))
    return commands


def generate_readme(cli_script, output_readme):
    """Generate the README.md file using OpenAI API."""
    # Step 1: Extract commands and arguments from CLI script
    commands = extract_argparse_commands(cli_script)

    # Template format for the README structure
    content = open("readme.tmpl", "r").read()

    # Prepare the final prompt to pass to OpenAI
    prompt = eval(f"f'''{content}'''")
    prompt.format(commands=commands)

    # Step 3: Initialize OpenAIProvider
    openai_provider = OpenAIProvider()

    # Step 4: Improve the README content using OpenAI
    readme_content = openai_provider.improve_text(
        """Update and improve this README template with the provided commands."""
        """Dont had trailing period to \"# headers\".  Let autofix as autofix.""",
        prompt,
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
# /* jscpd:ignore-end */
