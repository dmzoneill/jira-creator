#!/usr/bin/env python
"""
AI Helper plugin for jira-creator.

This plugin allows users to describe what they want in plain English,
and the AI will translate it into the appropriate Jira commands and execute them.
"""

import json
import os
import re
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_registry import PluginRegistry
from jira_creator.exceptions.exceptions import AIHelperError
from jira_creator.providers import get_ai_provider

logger = get_logger("ai_helper")


class AIHelperPlugin(JiraPlugin):
    """Plugin for natural language interaction with Jira."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "ai-helper"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Use natural language to interact with Jira"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Utilities"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return [
            'ai-helper "Add issue AAP-12345 to the current sprint"',
            'ai-helper "Set AAP-12345 to in progress and assign it to me"',
            'ai-helper "Create a bug for login page crash" --voice',
        ]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("prompt", help="Natural language description of what you want to do")
        parser.add_argument("--voice", action="store_true", help="Enable text-to-speech responses")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI processing (testing)")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the AI helper command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Get AI provider
            ai_provider = get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER"))

            # Load the AI helper prompt template
            system_prompt = self._load_template("aihelper")

            # Get all available plugin commands
            registry = PluginRegistry()
            registry.discover_plugins()
            plugin_names = registry.list_plugins()

            # Build command metadata for AI
            commands_metadata = self._build_command_metadata(registry, plugin_names)

            # Prepare full prompt
            full_prompt = (
                f"{system_prompt}\n\n" f"Available Commands:\n{commands_metadata}\n\n" f"User Request: {args.prompt}"
            )

            # Get AI response
            logger.info("Sending request to AI: %s", args.prompt)
            ai_response = ai_provider.improve_text(full_prompt, "")

            # Parse and execute commands
            steps = self._parse_ai_response(ai_response)

            if not steps:
                print("⚠️  AI couldn't understand the request. Try being more specific.")
                return False

            # Execute each step
            success = self._execute_steps(client, registry, steps, args.voice)
            return success

        except AIHelperError as e:
            logger.error("AI helper failed: %s", e)
            print(f"❌ AI helper failed: {e}")
            raise

    def _load_template(self, template_name: str) -> str:
        """
        Load a template file.

        Arguments:
            template_name: Name of the template file (without .tmpl extension)

        Returns:
            Template content as string
        """
        template_dir = Path(__file__).parent.parent / "templates"
        template_file = template_dir / f"{template_name}.tmpl"

        try:
            with open(template_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise AIHelperError(f"Template file not found: {template_file}") from e

    def _build_command_metadata(self, registry: PluginRegistry, plugin_names: List[str]) -> str:
        """
        Build metadata string describing all available commands.

        Arguments:
            registry: Plugin registry
            plugin_names: List of plugin names

        Returns:
            Formatted string with command metadata
        """
        metadata = []

        for name in sorted(plugin_names):
            plugin = registry.get_plugin(name)
            if not plugin:
                continue

            help_text = plugin.help_text if hasattr(plugin, "help_text") else ""
            metadata.append(f"  - {name}: {help_text}")

        return "\n".join(metadata)

    def _parse_ai_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """
        Parse AI response into structured steps.

        Arguments:
            ai_response: Raw AI response text

        Returns:
            List of step dictionaries
        """
        # Remove markdown code blocks
        cleaned = re.sub(r"^```(?:json)?|```$", "", ai_response.strip(), flags=re.MULTILINE).strip()

        try:
            result = json.loads(cleaned)

            # Handle error responses
            if isinstance(result, dict):
                if "error" in result:
                    logger.warning("AI returned error: %s", result["error"])
                    print(f"AI response: {result['error']}")
                    return []
                return []

            # Handle list of steps
            if isinstance(result, list):
                return result

            return []

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response: %s", e)
            logger.debug("Raw response: %s", cleaned[:500])
            raise AIHelperError(f"Failed to parse AI response: {e}") from e

    def _execute_steps(self, client: Any, registry: PluginRegistry, steps: List[Dict[str, Any]], voice: bool) -> bool:
        """
        Execute the steps returned by AI.

        Arguments:
            client: JiraClient instance
            registry: Plugin registry
            steps: List of step dictionaries
            voice: Whether to use text-to-speech

        Returns:
            bool: True if all steps succeeded
        """
        if not steps:
            print("No steps to execute")
            return False

        success_count = 0

        for step in steps:
            function_name = step.get("function", "")
            args_dict = step.get("args", {})
            action = step.get("action", "Executing command")

            print(f"\n🤖 {action}")
            print(f"   Command: {function_name}")
            print(f"   Arguments: {args_dict}")

            try:
                # Get the plugin
                plugin = registry.get_plugin(function_name)
                if not plugin:
                    logger.warning("Plugin not found: %s", function_name)
                    print(f"   ⚠️  Command '{function_name}' not found")
                    continue

                # Convert args dict to Namespace
                args = Namespace(**args_dict)

                # Execute the plugin
                plugin.execute(client, args)
                success_count += 1

                # Text-to-speech if requested
                if voice:
                    self._speak(action)

            except (ValueError, KeyError, AttributeError, AIHelperError) as e:
                logger.error("Failed to execute step %s: %s", function_name, e)
                print(f"   ❌ Failed: {e}")
                if voice:
                    self._speak(f"Failed: {e}")

        print(f"\n✅ Executed {success_count} of {len(steps)} steps successfully")
        return success_count > 0

    def _speak(self, text: str) -> None:
        """
        Convert text to speech using gTTS.

        Arguments:
            text: Text to speak
        """
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang="en")
            tts.save("/tmp/jira_tts.mp3")
            os.system("mpg123 /tmp/jira_tts.mp3 2>/dev/null")
        except ImportError:
            logger.warning("gTTS not installed, skipping text-to-speech")
        except (OSError, IOError) as e:
            logger.error("Text-to-speech failed: %s", e)

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        This plugin doesn't use REST operations directly.

        Arguments:
            client: JiraClient instance
            **kwargs: Additional arguments

        Returns:
            Empty dict
        """
        return {}
