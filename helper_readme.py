#!/usr/bin/env python
"""
Generate README.md based on current plugin-based architecture.

This module dynamically discovers all available plugins and generates
comprehensive documentation for the jira-creator CLI tool.
"""

import os
from argparse import ArgumentParser
from typing import List, Tuple

# Import the plugin system
from jira_creator.plugins import PluginRegistry
from jira_creator.providers import get_ai_provider


def extract_plugin_commands() -> str:
    """
    Extract commands and arguments from all discovered plugins.

    Returns:
        str: Formatted command documentation
    """
    registry = PluginRegistry()
    registry.discover_plugins()

    formatted_output = []

    # Sort plugins by command name for consistent output
    for command_name in sorted(registry._plugins.keys()):
        plugin = registry._plugins[command_name]

        # Create a temporary parser to extract arguments
        temp_parser = ArgumentParser()
        plugin.register_arguments(temp_parser)

        # Extract argument information
        arguments = []
        for action in temp_parser._actions:
            # Skip help and positional args that are added automatically
            if action.dest in ("help",):
                continue

            arg_names = action.option_strings if action.option_strings else [action.dest]
            arg_help = action.help if action.help else "No description available"

            arguments.append((arg_names, arg_help, action.required if hasattr(action, "required") else False))

        formatted_output.append(format_command(command_name, plugin.help_text, arguments))

    return "\n\n".join(formatted_output)


def format_command(command_name: str, help_text: str, arguments: List[Tuple]) -> str:
    """
    Format a command with its arguments into a human-readable string.

    Arguments:
        command_name: The command name
        help_text: Brief description of the command
        arguments: List of (arg_names, help_text, required) tuples

    Returns:
        str: Formatted command documentation
    """
    formatted_args = []

    for arg_names, arg_help, required in arguments:
        if isinstance(arg_names, list):
            arg_display = ", ".join(arg_names)
        else:
            arg_display = str(arg_names)

        required_text = " (required)" if required else ""
        arg_str = f"  - **{arg_display}**{required_text}: {arg_help}"
        formatted_args.append(arg_str)

    result = f"**{command_name}**\n{help_text}\n"
    if formatted_args:
        result += "\nArguments:\n" + "\n".join(formatted_args)

    return result


def create_basic_template() -> str:
    """
    Create a basic README template if none exists.

    Returns:
        str: Basic template content
    """
    return """# jira-creator

CLI and tools to automate JIRA issue creation with AI-powered enhancements.

## 🚀 Installation

```bash
pip install jira-creator
```

## ⚙️ Configuration

Set up your environment variables:

```bash
export JIRA_JPAT="your_jira_personal_access_token"
export JIRA_URL="https://your-jira-instance.com"
export JIRA_PROJECT_KEY="YOUR_PROJECT"
# ... other configuration variables
```

## 📚 Available Commands

==COMMANDS==

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the Apache License 2.0.
"""


def generate_readme(output_readme: str = "README.md") -> None:
    """
    Generate the README.md file using plugin discovery and AI enhancement.

    Arguments:
        output_readme: Output file path for the generated README
    """
    # Step 1: Extract commands and arguments from discovered plugins
    print("🔍 Discovering plugins...")
    commands = extract_plugin_commands()
    print(f"📋 Found {len(commands.split('**')) - 1} commands")

    # Step 2: Read template
    try:
        with open("readme.tmpl", "r") as f:
            template = f.read()
    except FileNotFoundError:
        print("❌ readme.tmpl not found. Creating basic template...")
        template = create_basic_template()

    # Step 3: Try to get AI provider for enhancement
    try:
        provider_name = os.getenv("JIRA_AI_PROVIDER", "openai")
        ai_provider = get_ai_provider(provider_name)

        # Step 4: Improve the README content using AI
        print("🤖 Enhancing commands documentation with AI...")
        commands = ai_provider.improve_text(
            """A user will provide you with a list of CLI commands and their arguments.
            Output improved README markdown **only** for the commands section.
            Be sure to provide:
            - Clear descriptions for each command and argument
            - Practical examples of how to use the commands
            - Any relevant tips to improve understanding of the tool
            - Use emojis sparingly for better readability
            - Provide detailed usage examples for complex commands
            """,
            commands,
        )

        print("🤖 Enhancing README template with AI...")
        template = ai_provider.improve_text(
            """Update and improve this README template for a modern CLI tool.
            Don't add trailing periods to "# headers".
            Keep "command-line" hyphenated.
            Remove trailing whitespace.
            Ensure the content is clear and professional.
            """,
            template,
        )

    except Exception as e:
        print(f"⚠️  AI enhancement failed: {e}")
        print("📝 Proceeding with basic documentation...")

    # Step 5: Replace placeholder with commands
    if "==COMMANDS==" in template:
        template = template.replace("==COMMANDS==", commands)
    else:
        # If no placeholder, append commands at the end
        template += "\n\n## 📚 Available Commands\n\n" + commands

    # Step 6: Write the README
    with open(output_readme, "w") as f:
        f.write(template)

    print(f"✅ README updated and saved to {output_readme}")


if __name__ == "__main__":
    # Generate README based on current plugin architecture
    generate_readme("README.md")
