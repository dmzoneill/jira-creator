#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) helper for interacting with an AI provider, specifically designed
to work with Jira. It allows users to query the AI for assistance with Jira commands and execute them accordingly.

Key Functions:
- `get_cli_command_metadata()`: Retrieves metadata about available CLI commands and their arguments.
- `call_function(client, function_name, args_dict)`: Invokes a specified function on the client with the provided
arguments.
- `clean_ai_output(ai_output: str)`: Cleans and parses the AI's output, removing markdown and converting it to a Python
object.
- `ask_ai_question(cli, ai_provider, system_prompt, user_prompt, voice=False)`: Sends a question to the AI and
processes the response, optionally providing voice feedback.
- `cli_ai_helper(cli, ai_provider, system_prompt, args)`: Main entry point for the CLI helper, orchestrating the
command metadata retrieval and AI interaction.

Dependencies:
- argparse: For parsing command-line arguments.
- json: For handling JSON data.
- os: For interacting with the operating system.
- re: For regular expression operations.
- gtts: For converting text to speech.

Exceptions:
- AIHelperError: Custom exception raised for errors related to AI helper operations.
"""

# pylint: disable=protected-access

import argparse
import json
import os
import re
from argparse import Namespace
from typing import Any, Dict, List, Union

from exceptions.exceptions import AIHelperError
from gtts import gTTS
from providers.ai_provider import AIProvider


def get_cli_command_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Retrieve the command metadata for the Jira Command Line Interface (CLI).

    Returns:
    dict: A dictionary where keys are command names and values are dictionaries containing information about the
    command, including help description and arguments.
    """

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    commands: Dict[str, Dict[str, Any]] = {}

    for name, subparser in subparsers.choices.items():
        command_info = {
            "help": subparser.description or subparser.prog,
            "arguments": [],
        }

        for action in subparser._actions:
            if action.dest in ("help", "command"):
                continue

            arg_info = {
                "name": action.dest,
                "required": action.required,
                "positional": not action.option_strings,
                "type": action.type.__name__ if action.type else "str",
                "help": action.help or "",
            }

            if not arg_info["positional"]:
                arg_info["flags"] = action.option_strings

            command_info["arguments"].append(arg_info)

        commands[name] = command_info

    return commands


def call_function(client: Any, function_name: str, args_dict: Dict[str, Any]) -> None:
    """
    Builds a fake argparse Namespace object using the provided arguments dictionary and assigns the given function name
    as the "command" attribute.

    Args:
    client: An object representing the client.
    function_name: A string specifying the name of the function to call.
    args_dict: A dictionary containing arguments to be used for building the Namespace object.
    """

    # Build a fake argparse Namespace (just like real CLI parsing would do)
    args = Namespace(**args_dict)
    setattr(args, "command", function_name)  # required for _dispatch_command

    # Dispatch through the existing dispatcher
    client._dispatch_command(args)


def clean_ai_output(ai_output: str) -> Union[List[Any], None]:
    """
    Remove Markdown-style code block wrappers from the AI output.

    Arguments:
    - ai_output (str): The AI output containing Markdown-style code block wrappers.

    Return:
    - list: A list of cleaned strings without Markdown-style code block wrappers.

    Exceptions:
    - ValueError: Raised if the cleaned string cannot be parsed into a JSON object.
    """

    # Remove any Markdown-style code block wrappers
    cleaned = re.sub(
        r"^```(?:json)?|```$", "", ai_output.strip(), flags=re.MULTILINE
    ).strip()

    # Parse JSON into Python object
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(e) from e


def ask_ai_question(
    cli: Any,
    ai_provider: AIProvider,
    system_prompt: str,
    user_prompt: str,
    voice: bool = False,
) -> bool:
    """
    Ask AI a question and generate steps based on the provided prompts.

    Args:
    cli: The cli object used to interact with the AI service.
    ai_provider: The AI provider object that provides the AI capabilities.
    system_prompt: The prompt representing the system's context for the AI question.
    user_prompt: The prompt representing the user's input for the AI question.
    voice (bool, optional): A flag indicating whether the AI response should be in voice format. Defaults to False.

    Return:
    bool: Indicates whether the AI question was successfully processed.
    """

    ai_raw = ai_provider.improve_text(system_prompt, user_prompt)
    ai_generated_steps = clean_ai_output(ai_raw)

    if isinstance(ai_generated_steps, dict):
        if "error" in ai_generated_steps:
            print("AI response: " + ai_generated_steps["error"])
            if voice:
                tts = gTTS(text=ai_generated_steps["error"], lang="en")
                tts.save("output.mp3")
                os.system("mpg123 output.mp3")
            return False
        print("Not sure: ")
        print(ai_generated_steps)
        return False

    if isinstance(ai_generated_steps, list):
        if len(ai_generated_steps) > 0:
            for step in ai_generated_steps:
                print(f"AI action: {step['action']}")
                print(f"Action: {step['function']}")
                print(f"   Changes: {step['args']}")
                call_function(cli, step["function"], step["args"])
                if voice:
                    tts = gTTS(text=step["action"], lang="en")
                    tts.save("output.mp3")
                    os.system("mpg123 output.mp3")
            return True
        print("No steps generated")
        return False

    return True


def cli_ai_helper(
    cli: Any, ai_provider: Any, system_prompt: str, args: Namespace
) -> bool:
    """
    Retrieve CLI command metadata using the 'get_cli_command_metadata' function.

    Arguments:
    - cli (object): The cli object used to interact with the CLI.
    - ai_provider (object): The AI provider object responsible for processing AI-related tasks.
    - system_prompt (str): The system prompt displayed to the user.
    - args (Namespace): Namespace object containing the command line arguments.

    Exceptions:
    - AIHelperError: Raised when there is an issue inspecting public methods of JiraCLI.
    """

    try:
        cli_commands = get_cli_command_metadata()

        commands = ""
        for cmd, info in cli_commands.items():
            cmd = cmd.replace("-", "_")
            commands += f"\n🔹 {cmd} \n"
            for arg in info["arguments"]:
                commands += f"  - {arg['name']} ({'positional' if arg['positional'] else 'optional'}) — {arg['help']}"

        ask_ai_question(
            cli,
            ai_provider,
            system_prompt,
            "\n\n" + commands + "\n\nQuestion: " + args.prompt,
            args.voice,
        )

        return True
    except AIHelperError as e:
        msg = f"❌ Failed to inspect public methods of JiraCLI: {e}"
        print(msg)
        raise AIHelperError(e) from e
