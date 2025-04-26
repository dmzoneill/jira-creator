import os
import re

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

        response = requests.post(self.endpoint, json=body, headers=headers, timeout=300)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()

        raise Exception(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )


def extract_argparse_commands(cli_script):
    with open(cli_script_path, "r") as f:
        lines = f.readlines()

    formatted_output = []
    current_command = None
    current_args = []

    # Regex patterns to match the command and argument lines
    command_pattern = re.compile(r'\s*(\w+)\s*=\s*add\("([^"]+)",\s*"([^"]+)"\)')
    argument_pattern = re.compile(r"\s*(\w+)\.add_argument\(([^)]+)\)")

    for line in lines:
        # Check for command definitions (e.g., ai_helper = add("ai-helper", "AI Helper"))
        command_match = command_pattern.match(line)
        if command_match:
            # If there was a previous command, add it to the formatted output
            if current_command:
                formatted_output.append(format_command(current_command, current_args))
            # Start a new command
            current_command = command_match.group(2)  # Command name (e.g., "ai-helper")
            current_args = []

        # Check for argument definitions (e.g., ai_helper.add_argument("prompt", help="A string..."))
        argument_match = argument_pattern.match(line)
        if argument_match:
            argument_name = argument_match.group(2).strip('"')
            argument_help = None
            # Look for help text in the argument definition
            help_match = re.search(r'help\s*=\s*"([^"]+)"', line)
            if help_match:
                argument_help = help_match.group(1)
            current_args.append((argument_name, argument_help))

    # Don't forget to append the last command and its arguments
    if current_command:
        formatted_output.append(format_command(current_command, current_args))

    return "\n\n".join(formatted_output)


def format_command(command_name, arguments):
    """Format a command with its arguments into a human-readable string."""
    formatted_args = []
    for arg, help_text in arguments:
        arg_str = f"  - **name**: {arg}"
        if help_text:
            arg_str += f"\n    - **help**: {help_text}"
        formatted_args.append(arg_str)

    return f"**{command_name}**:\n" + "\n".join(formatted_args)


def generate_readme(cli_script, output_readme):
    """Generate the README.md file using OpenAI API."""
    # Step 1: Extract commands and arguments from CLI script
    commands = extract_argparse_commands(cli_script)

    # Template format for the README structure
    template = open("readme.tmpl", "r").read()

    # Step 3: Initialize OpenAIProvider
    openai_provider = OpenAIProvider()

    # Step 4: Improve the README content using OpenAI
    commands = openai_provider.improve_text(
        """A user will provide you with a list of function signitures.
        Output README markdown **only**
        Be sure to provide:
        - Descriptions for each command and argument.
        - Examples of how to use the commands.
        - Any relevant explanations to improve understanding of the tool.
        - Add icons next to headers for look and feel
        - Provide fully detailed commands and argument and examples
        """,
        commands,
    )

    # Step 4: Improve the README content using OpenAI
    template = openai_provider.improve_text(
        """Update and improve this README template.
        Dont add trailing period to \"# headers\".
        Leave autofix as autofix.
        Leave \"command line\" be \"command-line\".
        Avoid trailing whitespace, remove where necessary.
        """,
        template,
    )

    # Prepare the final prompt to pass to OpenAI
    template = template.replace("==COMMANDS==", commands)

    # # Step 4: Improve the README content using OpenAI
    # template = openai_provider.improve_text(
    #     """I need you to create a table of contents for this readme.
    #     Pleace the TOC at "==TOC==" in the code.
    #     To achieve the TOC you will need to add anchors before headers.
    #     Headers are text proceeeded by 1+ # at the start of the line.
    #     E.g: <a name="desc"></a> and then in the TOC use markdown hyperlink format
    #     to link to these anchors. E.G "1. [ Description. ](#desc)".
    #     Here is a full exmaple:
    #         1. [ Description. ](#desc)
    #         2. [ Usage tips. ](#usage)
    #         <a name="desc"></a>
    #         ## 1. Description
    #         sometext
    #         <a name="usage"></a>
    #         ## 2. Usage tips
    #         sometext
    #     """,
    #     template,
    # )

    # Step 5: Write the new README content to the output file
    with open(output_readme, "w") as f:
        f.write(template)

    print(f"README updated and saved to {output_readme}")


if __name__ == "__main__":
    # Example usage
    cli_script_path = "jira_creator/rh_jira.py"
    output_readme_path = "README.md"
    generate_readme(cli_script_path, output_readme_path)
# /* jscpd:ignore-end */
