#!/usr/bin/env python
"""
Plugin-based CLI for jira-creator.

This is a demonstration of how the main CLI would work with the plugin
architecture. It can run alongside the existing CLI during migration.
"""

import os
import sys
from argparse import ArgumentParser, Namespace

import argcomplete

from jira_creator.plugins import PluginRegistry
from jira_creator.rest.client import JiraClient


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
            self.client = JiraClient()
        return self.client

    def run(self) -> None:
        """Run the CLI application."""
        # Set up argument parser
        prog_name = os.environ.get("CLI_NAME", os.path.basename(sys.argv[0]))
        parser = ArgumentParser(description="JIRA Issue Tool (Plugin-based)", prog=prog_name)

        subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

        # Discover and register plugins
        self.registry.discover_plugins()
        self.registry.register_all(subparsers)

        # Enable autocomplete
        argcomplete.autocomplete(parser)

        # Parse arguments
        args = parser.parse_args()

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
