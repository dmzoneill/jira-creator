"""Tests for the plugin-based CLI entry point, driven through run() and main()."""

from unittest.mock import Mock, patch

import pytest

from jira_creator.rh_jira import PluginBasedJiraCLI, main

MODULE = "jira_creator.rh_jira"


class FakeRegistry:
    """Plugin registry with a single 'test-command' plugin."""

    def __init__(self, plugin=None):
        self.plugin = plugin
        self.discovered = False
        self.injected = []

    def discover_plugins(self):
        """Record discovery."""
        self.discovered = True

    def register_all(self, subparsers):
        """Register the one command."""
        subparsers.add_parser("test-command", help="A test command")

    def list_plugins(self):
        """Names of the registered plugins."""
        return ["test-command"]

    def get_plugin(self, name):
        """Return the plugin for test-command, else None."""
        if self.plugin is not None:
            self.plugin.set_dependency.side_effect = lambda key, value: self.injected.append((key, value))
        return self.plugin if name == "test-command" else None


@pytest.fixture(name="cli")
def fixture_cli(monkeypatch):
    """Run the CLI with argv and a plugin; return (registry, client class, exit code)."""
    monkeypatch.delenv("CLI_NAME", raising=False)

    def run(argv, plugin=None, registry=None):
        registry = registry or FakeRegistry(plugin)
        with (
            patch(f"{MODULE}.PluginRegistry", return_value=registry),
            patch(f"{MODULE}.JiraClient") as client_cls,
            patch(f"{MODULE}.argcomplete.autocomplete") as autocomplete,
            patch("sys.argv", argv),
        ):
            code = None
            try:
                PluginBasedJiraCLI().run()
            except SystemExit as exc:
                code = exc.code
        return registry, client_cls, autocomplete, code

    return run


def plugin_returning(value=True, error=None):
    """Plugin whose execute() returns value or raises error."""
    plugin = Mock()
    plugin.help_text = "A test command"
    plugin.category = "ZZZ_Undefined"
    plugin.example_commands = ["test-command --flag"]
    plugin.execute.return_value = value
    if error is not None:
        plugin.execute.side_effect = error
    return plugin


class TestRun:
    """Parsing, discovery and dispatch through run()."""

    def test_init(self):
        """A new CLI has a registry and no client yet."""
        cli = PluginBasedJiraCLI()
        assert cli.registry is not None
        assert cli.client is None

    def test_success(self, cli):
        """A known command is executed with a client built from the registry."""
        plugin = plugin_returning(True)
        registry, client_cls, autocomplete, code = cli(["jira-cli", "test-command"], plugin)
        assert code is None
        assert registry.discovered
        autocomplete.assert_called_once()
        client_cls.assert_called_once_with(plugin_registry=registry)
        assert plugin.execute.call_args.args[0] is client_cls.return_value
        assert plugin.execute.call_args.args[1].command == "test-command"
        assert registry.injected == [("plugin_registry", registry)]

    @pytest.mark.parametrize(("env", "prog"), [({"CLI_NAME": "test-cli"}, "test-cli"), ({}, "jira-cli")])
    def test_prog_name(self, cli, monkeypatch, capsys, env, prog):
        """The program name comes from CLI_NAME, else argv[0]."""
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        code = cli(["/usr/bin/jira-cli"], plugin_returning())[3]
        assert code == 0
        assert prog in capsys.readouterr().out

    def test_no_command_shows_help(self, cli, capsys):
        """Without a command the fancy help is printed and the CLI exits 0."""
        code = cli(["jira-cli"], plugin_returning())[3]
        assert code == 0
        out = capsys.readouterr().out
        assert "test-command" in out
        assert "A test command" in out
        assert "ZZZ_Undefined" in out

    def test_help_flag(self, cli, capsys):
        """-h prints the fancy help listing the commands."""
        code = cli(["jira-cli", "-h"], plugin_returning())[3]
        assert code == 0
        assert "test-command" in capsys.readouterr().out


class TestDispatch:
    """Exit codes and messages from dispatching a command."""

    def test_unknown_command(self, cli, capsys):
        """A command with no plugin exits 1."""
        code = cli(["jira-cli", "test-command"], plugin=None)[3]
        assert code == 1
        assert "❌ Unknown command: test-command" in capsys.readouterr().out

    def test_plugin_failure(self, cli):
        """A plugin returning False exits 1."""
        assert cli(["jira-cli", "test-command"], plugin_returning(False))[3] == 1

    def test_keyboard_interrupt(self, cli, capsys):
        """Ctrl-C exits 130."""
        code = cli(["jira-cli", "test-command"], plugin_returning(error=KeyboardInterrupt()))[3]
        assert code == 130
        assert "⚠️  Operation cancelled by user" in capsys.readouterr().out

    def test_plugin_exception(self, cli, capsys):
        """Any other plugin error exits 1 with its message."""
        code = cli(["jira-cli", "test-command"], plugin_returning(error=ValueError("Test error")))[3]
        assert code == 1
        assert "❌ Command failed: Test error" in capsys.readouterr().out

    def test_client_is_cached(self):
        """The client is built once and reused across dispatches."""
        plugin = plugin_returning(True)
        registry = FakeRegistry(plugin)
        with (
            patch(f"{MODULE}.PluginRegistry", return_value=registry),
            patch(f"{MODULE}.JiraClient") as client_cls,
            patch(f"{MODULE}.argcomplete.autocomplete"),
            patch("sys.argv", ["jira-cli", "test-command"]),
        ):
            app = PluginBasedJiraCLI()
            app.run()
            app.run()
        client_cls.assert_called_once()
        assert plugin.execute.call_args_list[0].args[0] is plugin.execute.call_args_list[1].args[0]


def test_main():
    """main() builds the CLI and runs it."""
    with patch(f"{MODULE}.PluginBasedJiraCLI") as cli_cls:
        main()
    cli_cls.return_value.run.assert_called_once_with()
