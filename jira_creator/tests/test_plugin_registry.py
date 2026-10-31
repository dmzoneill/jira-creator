"""
Tests for PluginRegistry registration of plugin exceptions, AI prompts and field mappings.

Plugins are registered through the public discover_plugins() path.
"""

import sys
import types
from argparse import ArgumentParser
from typing import ClassVar

import pytest

from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_config import FieldMapping
from jira_creator.core.plugin_registry import PluginRegistry
from jira_creator.plugins.create_issue_plugin import CreateIssuePlugin

FAKE_MODULE = "jira_creator.plugins.fake_registry_plugin"


class MockPluginError(Exception):
    """Mock exception for plugin testing."""


class StubPlugin(JiraPlugin):
    """Minimal concrete plugin; subclasses set what it registers."""

    command = "stub"
    exceptions: ClassVar[dict] = {}
    prompts: ClassVar[dict] = {}
    mappings: ClassVar[dict] = {}

    @property
    def command_name(self):
        """Command name."""
        return self.command

    @property
    def help_text(self):
        """Help text."""
        return f"Test plugin {self.command}"

    def register_arguments(self, parser: ArgumentParser):
        """Register no arguments."""
        del parser

    def execute(self, client, args):
        """Succeed without doing anything."""
        del client, args
        return True

    def rest_operation(self, client, **kwargs):
        """Return an empty response."""
        del client, kwargs
        return {}

    def get_plugin_exceptions(self):
        """Exceptions this plugin registers."""
        return dict(self.exceptions)

    def get_ai_prompts(self):
        """AI prompts this plugin registers."""
        return dict(self.prompts)

    def get_field_mappings(self):
        """Field mappings this plugin registers."""
        return dict(self.mappings)


def make_plugin(command, exceptions=None, prompts=None, mappings=None):
    """A StubPlugin subclass registering the given items."""
    attrs = {
        "command": command,
        "exceptions": exceptions or {},
        "prompts": prompts or {},
        "mappings": mappings or {},
    }
    return type(f"Plugin_{command.replace('-', '_')}", (StubPlugin,), attrs)


@pytest.fixture(name="load")
def fixture_load(tmp_path, monkeypatch):
    """Build a registry by discovering the given plugin classes from a plugin dir."""

    def load(*classes):
        module = types.ModuleType(FAKE_MODULE)
        for cls in classes:
            setattr(module, cls.__name__, cls)
        monkeypatch.setitem(sys.modules, FAKE_MODULE, module)
        (tmp_path / "fake_registry_plugin.py").write_text("", encoding="utf-8")
        registry = PluginRegistry()
        registry.discover_plugins(str(tmp_path))
        return registry

    return load


class TestPluginRegistry:
    """Tests for PluginRegistry exception registration."""

    def test_registry_initializes_with_empty_exceptions(self):
        """Test that registry initializes with empty exception dict."""
        registry = PluginRegistry()
        assert isinstance(registry.list_exceptions(), dict) and not registry.list_exceptions()

    def test_get_exception_returns_none_for_missing(self):
        """Test that get_exception returns None for non-existent exception."""
        registry = PluginRegistry()
        assert registry.get_exception("NonExistent") is None

    def test_plugin_exception_registration(self, load):
        """A discovered plugin's exceptions are registered."""
        registry = load(make_plugin("test-exception-plugin", exceptions={"MockPluginError": MockPluginError}))
        assert "MockPluginError" in registry.list_exceptions()
        assert registry.get_exception("MockPluginError") == MockPluginError

    def test_get_all_exceptions_alias(self, load):
        """Test that get_all_exceptions is an alias for list_exceptions."""
        registry = load(make_plugin("p", exceptions={"TestError": MockPluginError}))
        assert registry.get_all_exceptions() == registry.list_exceptions()
        assert "TestError" in registry.get_all_exceptions()

    def test_clear_removes_exceptions(self, load):
        """Test that clear() removes all exceptions."""
        registry = load(make_plugin("p", exceptions={"TestError": MockPluginError}))
        assert "TestError" in registry.list_exceptions()
        registry.clear()
        assert isinstance(registry.list_exceptions(), dict) and not registry.list_exceptions()

    def test_list_exceptions_returns_copy(self, load):
        """Test that list_exceptions returns a copy, not reference."""
        registry = load(make_plugin("p", exceptions={"TestError": MockPluginError}))
        exceptions_list = registry.list_exceptions()
        exceptions_list["NewError"] = Exception
        assert "NewError" not in registry.list_exceptions()
        assert "TestError" in registry.list_exceptions()

    def test_plugin_without_exceptions_works(self, load):
        """Test that plugins without exceptions don't break registration."""
        registry = load(make_plugin("test-no-exception-plugin"))
        assert registry.list_plugins() == ["test-no-exception-plugin"]
        assert isinstance(registry.list_exceptions(), dict) and not registry.list_exceptions()

    def test_multiple_plugins_with_exceptions(self, load):
        """Test registering exceptions from multiple plugins."""

        class PluginError1(Exception):
            """First plugin error."""

        class PluginError2(Exception):
            """Second plugin error."""

        registry = load(
            make_plugin("plugin1", exceptions={"PluginError1": PluginError1}),
            make_plugin("plugin2", exceptions={"PluginError2": PluginError2}),
        )
        exceptions = registry.list_exceptions()
        assert exceptions == {"PluginError1": PluginError1, "PluginError2": PluginError2}

    def test_create_issue_plugin_registers_exception(self):
        """Test that CreateIssuePlugin properly registers CreateIssueError."""
        assert "CreateIssueError" in CreateIssuePlugin().get_plugin_exceptions()


class TestPluginAIPrompts:
    """Tests for plugin AI prompt registration."""

    def test_registry_initializes_with_empty_prompts(self):
        """Test that registry initializes with empty AI prompts dict."""
        registry = PluginRegistry()
        assert isinstance(registry.get_all_ai_prompts(), dict) and not registry.get_all_ai_prompts()

    def test_get_ai_prompts_returns_empty_for_missing_plugin(self):
        """Test that get_ai_prompts returns empty dict for non-existent plugin."""
        registry = PluginRegistry()
        prompts = registry.get_ai_prompts("non-existent")
        assert isinstance(prompts, dict) and not prompts

    def test_plugin_ai_prompts_registration(self, load):
        """Test registering AI prompts from a plugin."""
        prompts = {
            "task": "As a professional engineer, write clear task descriptions.",
            "story": "As a professional engineer, write user stories.",
        }
        registry = load(make_plugin("test-prompts", prompts=prompts))
        registered = registry.get_ai_prompts("test-prompts")
        assert registered == prompts
        assert "professional engineer" in registered["task"]

    def test_plugin_without_prompts_not_listed(self, load):
        """A plugin with no prompts adds no entry."""
        registry = load(make_plugin("plain"))
        assert not registry.get_all_ai_prompts()

    def test_get_all_ai_prompts(self, load):
        """Test getting all AI prompts from all plugins."""
        registry = load(
            make_plugin("plugin1", prompts={"prompt1": "Prompt 1 text"}),
            make_plugin("plugin2", prompts={"prompt2": "Prompt 2 text"}),
        )
        assert registry.get_all_ai_prompts() == {
            "plugin1": {"prompt1": "Prompt 1 text"},
            "plugin2": {"prompt2": "Prompt 2 text"},
        }

    def test_clear_removes_ai_prompts(self, load):
        """Test that clear() removes all AI prompts."""
        registry = load(make_plugin("test", prompts={"prompt": "text"}))
        assert len(registry.get_all_ai_prompts()) == 1
        registry.clear()
        assert isinstance(registry.get_all_ai_prompts(), dict) and not registry.get_all_ai_prompts()

    def test_create_issue_plugin_has_ai_prompts(self):
        """Test that CreateIssuePlugin registers AI prompts."""
        prompts = CreateIssuePlugin().get_ai_prompts()
        assert {"task", "story", "bug", "epic"} <= set(prompts)


class TestPluginFieldMappings:
    """Tests for plugin field mapping registration."""

    def test_registry_initializes_with_empty_field_mappings(self):
        """Test that registry initializes with empty field mappings dict."""
        registry = PluginRegistry()
        assert isinstance(registry.get_all_field_mappings(), dict) and not registry.get_all_field_mappings()

    def test_get_field_mappings_returns_empty_for_missing_plugin(self):
        """Test that get_field_mappings returns empty dict for non-existent plugin."""
        mappings = PluginRegistry().get_field_mappings("non-existent")
        assert isinstance(mappings, dict) and not mappings

    def test_plugin_field_mappings_registration(self, load):
        """Test registering field mappings from a plugin."""
        mappings = {
            "epic": FieldMapping(
                env_var="JIRA_EPIC_FIELD",
                default="customfield_12311140",
                required=False,
                description="Epic link field",
            ),
            "story_points": FieldMapping(
                env_var="JIRA_STORY_POINTS_FIELD",
                default="customfield_12310243",
                required=True,
                description="Story points field",
            ),
        }
        registry = load(make_plugin("test-fields", mappings=mappings))
        registered = registry.get_field_mappings("test-fields")
        assert set(registered) == {"epic", "story_points"}
        assert registered["epic"].env_var == "JIRA_EPIC_FIELD"
        assert registered["epic"].default == "customfield_12311140"
        assert not registered["epic"].required
        assert registered["story_points"].required

    def test_get_all_field_mappings(self, load):
        """Test getting all field mappings from all plugins."""
        field1 = FieldMapping(env_var="FIELD1", default="default1", required=False, description="Field 1")
        field2 = FieldMapping(env_var="FIELD2", default="default2", required=True, description="Field 2")
        registry = load(
            make_plugin("plugin1", mappings={"field1": field1}),
            make_plugin("plugin2", mappings={"field2": field2}),
        )
        all_mappings = registry.get_all_field_mappings()
        assert set(all_mappings) == {"plugin1", "plugin2"}
        assert all_mappings["plugin1"]["field1"].env_var == "FIELD1"
        assert all_mappings["plugin2"]["field2"].env_var == "FIELD2"

    def test_clear_removes_field_mappings(self, load):
        """Test that clear() removes all field mappings."""
        field = FieldMapping(env_var="TEST", description="Test field")
        registry = load(make_plugin("test", mappings={"field": field}))
        assert len(registry.get_all_field_mappings()) == 1
        registry.clear()
        assert isinstance(registry.get_all_field_mappings(), dict) and not registry.get_all_field_mappings()

    def test_create_issue_plugin_has_field_mappings(self):
        """Test that CreateIssuePlugin registers field mappings."""
        mappings = CreateIssuePlugin().get_field_mappings()
        assert mappings["epic"].env_var == "JIRA_EPIC_FIELD"
        assert mappings["story_points"].env_var == "JIRA_STORY_POINTS_FIELD"
