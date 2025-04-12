import argparse
import json
import os
import re
from argparse import Namespace

from exceptions.exceptions import AIHelperError
from gtts import gTTS


def get_cli_command_metadata():
    from rh_jira import JiraCLI  # ← moved inside

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    # Create CLI instance and register subcommands
    cli = JiraCLI()
    cli._register_subcommands(subparsers)

    commands = {}

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


def call_function(client, function_name, args_dict):
    # Build a fake argparse Namespace (just like real CLI parsing would do)
    args = Namespace(**args_dict)
    setattr(args, "command", function_name)  # required for _dispatch_command

    # Dispatch through the existing dispatcher
    client._dispatch_command(args)


def clean_ai_output(ai_output: str) -> list:
    # Remove any Markdown-style code block wrappers
    cleaned = re.sub(
        r"^```(?:json)?|```$", "", ai_output.strip(), flags=re.MULTILINE
    ).strip()

    # Parse JSON into Python object
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse AI response as JSON: {e}\nRaw cleaned text:\n{cleaned}"
        )


def ask_ai_question(client, ai_provider, system_prompt, user_prompt, voice=False):
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
        else:
            print("Not sure: ")
            print(ai_generated_steps)
            return

    if isinstance(ai_generated_steps, list):
        if len(ai_generated_steps) > 0:
            for step in ai_generated_steps:
                print("AI action: {action}".format(action=step["action"]))
                print("Action: {action}".format(action=step["function"]))
                print("   Changes: {changes}".format(changes=step["args"]))
                call_function(client, step["function"], step["args"])
                if voice:
                    tts = gTTS(text=step["action"], lang="en")
                    tts.save("output.mp3")
                    os.system("mpg123 output.mp3")
        else:
            print("No steps generated")
            return False


def cli_ai_helper(client, ai_provider, system_prompt, args):
    try:
        cli_commands = get_cli_command_metadata()

        commands = ""
        for cmd, info in cli_commands.items():
            cmd = cmd.replace("-", "_")
            commands += f"\n🔹 {cmd} \n"
            for arg in info["arguments"]:
                commands += f"  - {arg['name']} ({'positional' if arg['positional'] else 'optional'}) — {arg['help']}"

        ask_ai_question(
            client,
            ai_provider,
            system_prompt,
            "\n\n" + commands + "\n\nQuestion: " + args.prompt,
            args.voice,
        )

        return True
    except AIHelperError as e:
        msg = f"❌ Failed to inspect public methods of JiraCLI: {e}"
        print(msg)
        raise AIHelperError(msg)
