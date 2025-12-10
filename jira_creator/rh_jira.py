#!/usr/bin/env python
"""
Plugin-based CLI for jira-creator.

This is a demonstration of how the main CLI would work with the plugin
architecture. It can run alongside the existing CLI during migration.
"""

import os
import sys
from argparse import Action, ArgumentParser, Namespace

import argcomplete

from jira_creator.core.plugin_registry import PluginRegistry
from jira_creator.rest.client import JiraClient

# ANSI color codes
COLORS = {
    "BOLD": "\033[1m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "RED": "\033[91m",
    "RESET": "\033[0m",
    "DIM": "\033[2m",
}

ASCII_BANNER = r"""
     _ ___ ____      _      ____ ____  _____    _  _____ ___  ____
    | |_ _|  _ \    / \    / ___|  _ \| ____|  / \|_   _/ _ \|  _ \
 _  | || || |_) |  / _ \  | |   | |_) |  _|   / _ \ | || | | | |_) |
| |_| || ||  _ <  / ___ \ | |___|  _ <| |___ / ___ \| || |_| |  _ <
 \___/|___|_| \_\/_/   \_\ \____|_| \_\_____/_/   \_\_| \___/|_| \_\

                   AI-Powered Issue Management 🚀
"""

# Category display order (categories not in this list will appear last)
CATEGORY_ORDER = [
    "Issue Creation & Management",
    "Search & View",
    "Issue Modification",
    "Sprint Management",
    "Issue Relationships",
    "Blocking & Issues",
    "Quality & Validation",
    "Reporting",
    "Utilities",
    "Other",
]

# Category emoji mappings
CATEGORY_EMOJIS = {
    "Issue Creation & Management": "📝",
    "Search & View": "🔍",
    "Issue Modification": "✏️ ",
    "Sprint Management": "🎯",
    "Issue Relationships": "🔗",
    "Blocking & Issues": "🚧",
    "Quality & Validation": "✅",
    "Reporting": "📊",
    "Utilities": "🛠️ ",
    "Other": "📦",
}


class FancyHelpAction(Action):
    """Custom help action that displays fancy formatted help."""

    def __init__(self, option_strings, dest, default=False, help=None):  # pylint: disable=redefined-builtin
        super().__init__(option_strings, dest, 0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        """Display fancy help and exit."""
        _print_fancy_help(parser)
        parser.exit()


def _print_command_examples(plugin, prog_name):
    """Print examples for a command."""
    if plugin and hasattr(plugin, "example_commands"):
        examples = plugin.example_commands
        if examples:
            dim = COLORS["DIM"]
            reset = COLORS["RESET"]
            cyan = COLORS["CYAN"]
            for example in examples:
                print(f"      {dim}${reset} {cyan}{prog_name}{reset} {example}")


def _print_commands(registry, plugin_names, prog_name):
    """Print command categories and examples."""
    # Build categories dynamically from plugin metadata
    categories = {}
    for cmd in plugin_names:
        plugin = registry.get_plugin(cmd)
        if plugin:
            category = plugin.category if hasattr(plugin, "category") else "Other"
            if category not in categories:
                categories[category] = []
            categories[category].append(cmd)

    # Sort categories by defined order
    def category_sort_key(cat):
        try:
            return CATEGORY_ORDER.index(cat)
        except ValueError:
            return len(CATEGORY_ORDER)  # Put undefined categories at the end

    for category in sorted(categories.keys(), key=category_sort_key):
        commands = sorted(categories[category])  # Sort commands alphabetically within category

        # Add emoji if defined
        emoji = CATEGORY_EMOJIS.get(category, "")
        display_category = f"{emoji} {category}" if emoji else category

        print(f"  {COLORS['BOLD']}{display_category}{COLORS['RESET']}")
        for idx, cmd in enumerate(commands):
            # Add spacing before command (except first)
            if idx > 0:
                print()

            plugin = registry.get_plugin(cmd)
            help_text = plugin.help_text if plugin and hasattr(plugin, "help_text") else ""
            # Truncate long help text
            if len(help_text) > 60:
                help_text = help_text[:57] + "..."
            print(f"    {COLORS['GREEN']}{cmd:30s}{COLORS['RESET']} {COLORS['DIM']}{help_text}{COLORS['RESET']}")

            # Print examples if available
            _print_command_examples(plugin, prog_name)
        print()


def _print_fancy_help(parser):
    """Print fancy formatted help output."""
    # Print ASCII banner
    print(f"{COLORS['CYAN']}{ASCII_BANNER}{COLORS['RESET']}")

    # Print description
    print(f"\n{COLORS['BOLD']}{COLORS['GREEN']}DESCRIPTION{COLORS['RESET']}")
    print(f"  {COLORS['DIM']}A powerful CLI tool for managing JIRA issues with AI-powered")
    print(f"  quality checks, automated fixes, and streamlined workflows.{COLORS['RESET']}\n")

    # Get all plugins
    registry = PluginRegistry()
    registry.discover_plugins()
    plugin_names = sorted(registry.list_plugins())

    # Print usage
    prog_name = parser.prog
    print(f"{COLORS['BOLD']}{COLORS['YELLOW']}USAGE{COLORS['RESET']}")
    print(
        f"  {COLORS['CYAN']}{prog_name}{COLORS['RESET']} {COLORS['DIM']}<command>{COLORS['RESET']} "
        f"{COLORS['DIM']}[options]{COLORS['RESET']}\n"
    )

    # Print categorized commands
    print(f"{COLORS['BOLD']}{COLORS['YELLOW']}COMMANDS{COLORS['RESET']}\n")
    _print_commands(registry, plugin_names, prog_name)

    # Print additional options
    print(f"{COLORS['BOLD']}{COLORS['YELLOW']}OPTIONS{COLORS['RESET']}")
    print(
        f"  {COLORS['GREEN']}-h, --help{COLORS['RESET']}              "
        f"{COLORS['DIM']}Show this help message and exit{COLORS['RESET']}"
    )
    print()

    # Print footer
    print(f"{COLORS['DIM']}{'─' * 79}{COLORS['RESET']}")
    print(f"{COLORS['DIM']}For more information, visit: https://github.com/dmzoneill/jira-creator{COLORS['RESET']}\n")


class PluginBasedJiraCLI:
    """Main CLI class using plugin architecture."""

    def __init__(self):
        """Initialize the CLI with plugin registry and client."""
        self.registry = PluginRegistry()
        self.client = None  # Initialized when needed

    def _get_client(self) -> JiraClient:
        """Get or create JiraClient instance."""
        if self.client is None:
            # Initialize client - it gets configuration from environment variables
            # Pass the registry so the client can reload plugins after AI fixes
            self.client = JiraClient(plugin_registry=self.registry)
        return self.client

    def run(self) -> None:
        """Run the CLI application."""
        # Set up argument parser with custom help
        prog_name = os.environ.get("CLI_NAME", os.path.basename(sys.argv[0]))
        parser = ArgumentParser(
            description="JIRA Issue Tool (Plugin-based)", prog=prog_name, add_help=False  # Disable default help
        )

        # Add custom help action
        parser.add_argument("-h", "--help", action=FancyHelpAction, help="Show this help message and exit")

        subparsers = parser.add_subparsers(dest="command", required=False, help="Available commands")

        # Discover and register plugins
        self.registry.discover_plugins()
        self.registry.register_all(subparsers)

        # Enable autocomplete
        argcomplete.autocomplete(parser)

        # Parse arguments
        args = parser.parse_args()

        # If no command specified, show help
        if not args.command:
            _print_fancy_help(parser)
            sys.exit(0)

        # Dispatch to plugin
        self._dispatch_command(args)

    def _dispatch_command(self, args: Namespace) -> None:
        """
        Dispatch command to appropriate plugin.

        Arguments:
            args: Parsed command line arguments
        """
        # Get the plugin for this command
        plugin = self.registry.get_plugin(args.command)

        if plugin is None:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)

        try:
            # Inject plugin registry as a dependency (for AI fix functionality)
            plugin.set_dependency("plugin_registry", self.registry)

            # Execute the plugin
            client = self._get_client()
            success = plugin.execute(client, args)

            if not success:
                sys.exit(1)

        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            sys.exit(130)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"❌ Command failed: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    cli = PluginBasedJiraCLI()
    cli.run()


if __name__ == "__main__":
    main()
