#!/usr/bin/env python
"""
Tests for the PluginRegistry functionality.
"""

from argparse import ArgumentParser

from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_config import FieldMapping
from jira_creator.core.plugin_registry import PluginRegistry
from jira_creator.plugins.create_issue_plugin import CreateIssueError, CreateIssuePlugin


class MockPluginError(Exception):
    """Mock exception for plugin testing."""


class MockPluginWithException(JiraPlugin):
    """Mock plugin that registers an exception."""

    @property
    def command_name(self):
        return "test-exception-plugin"

    @property
    def help_text(self):
        return "Test plugin with exception"

    def register_arguments(self, parser: ArgumentParser):
        pass

    def execute(self, client, args):
        return True

    def rest_operation(self, client, **kwargs):
        return {}

    def get_plugin_exceptions(self):
        """Register test exception."""
        return {
            "MockPluginError": MockPluginError,
        }


class MockPluginNoException(JiraPlugin):
    """Mock plugin that doesn't register any exceptions."""

    @property
    def command_name(self):
        return "test-no-exception-plugin"

    @property
    def help_text(self):
        return "Test plugin without exception"

    def register_arguments(self, parser: ArgumentParser):
        pass

    def execute(self, client, args):
        return True

    def rest_operation(self, client, **kwargs):
        return {}


class TestPluginRegistry:
    """Tests for PluginRegistry exception registration."""

    def test_registry_initializes_with_empty_exceptions(self):
        """Test that registry initializes with empty exception dict."""
        registry = PluginRegistry()
        assert registry.list_exceptions() == {}

    def test_get_exception_returns_none_for_missing(self):
        """Test that get_exception returns None for non-existent exception."""
        registry = PluginRegistry()
        assert registry.get_exception("NonExistent") is None

    def test_manual_exception_registration(self):
        """Test manually registering an exception via plugin."""
        registry = PluginRegistry()

        # Manually add a plugin with exception
        plugin = MockPluginWithException()
        command_name = plugin.command_name
        registry._plugins[command_name] = plugin
        registry._plugin_classes[command_name] = MockPluginWithException

        # Register exceptions manually
        plugin_exceptions = plugin.get_plugin_exceptions()
        for exc_name, exc_class in plugin_exceptions.items():
            registry._exceptions[exc_name] = exc_class

        # Verify exception was registered
        assert "MockPluginError" in registry.list_exceptions()
        assert registry.get_exception("MockPluginError") == MockPluginError

    def test_get_all_exceptions_alias(self):
        """Test that get_all_exceptions is an alias for list_exceptions."""
        registry = PluginRegistry()

        # Add an exception directly
        registry._exceptions["TestError"] = MockPluginError

        # Both methods should return the same result
        assert registry.get_all_exceptions() == registry.list_exceptions()
        assert "TestError" in registry.get_all_exceptions()

    def test_clear_removes_exceptions(self):
        """Test that clear() removes all exceptions."""
        registry = PluginRegistry()

        # Add an exception
        registry._exceptions["TestError"] = MockPluginError

        # Verify it exists
        assert "TestError" in registry.list_exceptions()

        # Clear the registry
        registry.clear()

        # Verify exceptions are cleared
        assert registry.list_exceptions() == {}

    def test_list_exceptions_returns_copy(self):
        """Test that list_exceptions returns a copy, not reference."""
        registry = PluginRegistry()
        registry._exceptions["TestError"] = MockPluginError

        # Get the list
        exceptions_list = registry.list_exceptions()

        # Modify the returned list
        exceptions_list["NewError"] = Exception

        # Original should be unchanged
        assert "NewError" not in registry.list_exceptions()
        assert "TestError" in registry.list_exceptions()

    def test_plugin_without_exceptions_works(self):
        """Test that plugins without exceptions don't break registration."""
        registry = PluginRegistry()

        plugin = MockPluginNoException()
        command_name = plugin.command_name
        registry._plugins[command_name] = plugin
        registry._plugin_classes[command_name] = MockPluginNoException

        # Get exceptions (should be empty)
        plugin_exceptions = plugin.get_plugin_exceptions()

        # This should not raise an error
        for exc_name, exc_class in plugin_exceptions.items():
            registry._exceptions[exc_name] = exc_class

        # No exceptions should be registered
        assert registry.list_exceptions() == {}

    def test_multiple_plugins_with_exceptions(self):
        """Test registering exceptions from multiple plugins."""

        class PluginError1(Exception):
            """First plugin error."""

        class PluginError2(Exception):
            """Second plugin error."""

        class Plugin1(JiraPlugin):
            @property
            def command_name(self):
                return "plugin1"

            @property
            def help_text(self):
                return "Plugin 1"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_plugin_exceptions(self):
                return {"PluginError1": PluginError1}

        class Plugin2(JiraPlugin):
            @property
            def command_name(self):
                return "plugin2"

            @property
            def help_text(self):
                return "Plugin 2"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_plugin_exceptions(self):
                return {"PluginError2": PluginError2}

        registry = PluginRegistry()

        # Register both plugins
        for plugin_class in [Plugin1, Plugin2]:
            plugin = plugin_class()
            command_name = plugin.command_name
            registry._plugins[command_name] = plugin
            registry._plugin_classes[command_name] = plugin_class

            # Register exceptions
            plugin_exceptions = plugin.get_plugin_exceptions()
            for exc_name, exc_class in plugin_exceptions.items():
                registry._exceptions[exc_name] = exc_class

        # Verify both exceptions are registered
        exceptions = registry.list_exceptions()
        assert len(exceptions) == 2
        assert "PluginError1" in exceptions
        assert "PluginError2" in exceptions
        assert exceptions["PluginError1"] == PluginError1
        assert exceptions["PluginError2"] == PluginError2

    def test_create_issue_plugin_registers_exception(self):
        """Test that CreateIssuePlugin properly registers CreateIssueError."""
        plugin = CreateIssuePlugin()

        # Get plugin exceptions
        exceptions = plugin.get_plugin_exceptions()

        # Verify CreateIssueError is registered
        assert "CreateIssueError" in exceptions
        assert exceptions["CreateIssueError"] == CreateIssueError
        assert issubclass(exceptions["CreateIssueError"], Exception)


class TestPluginAIPrompts:
    """Tests for plugin AI prompt registration."""

    def test_registry_initializes_with_empty_prompts(self):
        """Test that registry initializes with empty AI prompts dict."""
        registry = PluginRegistry()
        assert registry.get_all_ai_prompts() == {}

    def test_get_ai_prompts_returns_empty_for_missing_plugin(self):
        """Test that get_ai_prompts returns empty dict for non-existent plugin."""
        registry = PluginRegistry()
        assert registry.get_ai_prompts("non-existent") == {}

    def test_plugin_ai_prompts_registration(self):
        """Test registering AI prompts from a plugin."""

        class PluginWithPrompts(JiraPlugin):
            @property
            def command_name(self):
                return "test-prompts"

            @property
            def help_text(self):
                return "Test plugin with prompts"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_ai_prompts(self):
                return {
                    "task": "As a professional engineer, write clear task descriptions.",
                    "story": "As a professional engineer, write user stories.",
                }

        registry = PluginRegistry()
        plugin = PluginWithPrompts()
        command_name = plugin.command_name

        # Manually register plugin and prompts
        registry._plugins[command_name] = plugin
        plugin_prompts = plugin.get_ai_prompts()
        if plugin_prompts:
            registry._ai_prompts[command_name] = plugin_prompts

        # Verify prompts are registered
        prompts = registry.get_ai_prompts("test-prompts")
        assert len(prompts) == 2
        assert "task" in prompts
        assert "story" in prompts
        assert "professional engineer" in prompts["task"]

    def test_get_all_ai_prompts(self):
        """Test getting all AI prompts from all plugins."""

        class Plugin1(JiraPlugin):
            @property
            def command_name(self):
                return "plugin1"

            @property
            def help_text(self):
                return "Plugin 1"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_ai_prompts(self):
                return {"prompt1": "Prompt 1 text"}

        class Plugin2(JiraPlugin):
            @property
            def command_name(self):
                return "plugin2"

            @property
            def help_text(self):
                return "Plugin 2"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_ai_prompts(self):
                return {"prompt2": "Prompt 2 text"}

        registry = PluginRegistry()

        for plugin_class in [Plugin1, Plugin2]:
            plugin = plugin_class()
            command_name = plugin.command_name
            registry._plugins[command_name] = plugin
            plugin_prompts = plugin.get_ai_prompts()
            if plugin_prompts:
                registry._ai_prompts[command_name] = plugin_prompts

        # Verify all prompts are accessible
        all_prompts = registry.get_all_ai_prompts()
        assert len(all_prompts) == 2
        assert "plugin1" in all_prompts
        assert "plugin2" in all_prompts
        assert all_prompts["plugin1"]["prompt1"] == "Prompt 1 text"
        assert all_prompts["plugin2"]["prompt2"] == "Prompt 2 text"

    def test_clear_removes_ai_prompts(self):
        """Test that clear() removes all AI prompts."""
        registry = PluginRegistry()
        registry._ai_prompts["test"] = {"prompt": "text"}

        assert len(registry.get_all_ai_prompts()) == 1

        registry.clear()

        assert registry.get_all_ai_prompts() == {}

    def test_create_issue_plugin_has_ai_prompts(self):
        """Test that CreateIssuePlugin registers AI prompts."""
        plugin = CreateIssuePlugin()
        prompts = plugin.get_ai_prompts()

        # Verify prompts for different issue types
        assert "task" in prompts
        assert "story" in prompts
        assert "bug" in prompts
        assert "epic" in prompts


class TestPluginFieldMappings:
    """Tests for plugin field mapping registration."""

    def test_registry_initializes_with_empty_field_mappings(self):
        """Test that registry initializes with empty field mappings dict."""
        registry = PluginRegistry()
        assert registry.get_all_field_mappings() == {}

    def test_get_field_mappings_returns_empty_for_missing_plugin(self):
        """Test that get_field_mappings returns empty dict for non-existent plugin."""
        registry = PluginRegistry()
        assert registry.get_field_mappings("non-existent") == {}

    def test_plugin_field_mappings_registration(self):
        """Test registering field mappings from a plugin."""

        class PluginWithFields(JiraPlugin):
            @property
            def command_name(self):
                return "test-fields"

            @property
            def help_text(self):
                return "Test plugin with field mappings"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_field_mappings(self):
                return {
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

        registry = PluginRegistry()
        plugin = PluginWithFields()
        command_name = plugin.command_name

        # Manually register plugin and field mappings
        registry._plugins[command_name] = plugin
        field_mappings = plugin.get_field_mappings()
        if field_mappings:
            registry._field_mappings[command_name] = field_mappings

        # Verify field mappings are registered
        mappings = registry.get_field_mappings("test-fields")
        assert len(mappings) == 2
        assert "epic" in mappings
        assert "story_points" in mappings
        assert mappings["epic"].env_var == "JIRA_EPIC_FIELD"
        assert mappings["epic"].default == "customfield_12311140"
        assert not mappings["epic"].required
        assert mappings["story_points"].required

    def test_get_all_field_mappings(self):
        """Test getting all field mappings from all plugins."""

        class Plugin1(JiraPlugin):
            @property
            def command_name(self):
                return "plugin1"

            @property
            def help_text(self):
                return "Plugin 1"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_field_mappings(self):
                return {
                    "field1": FieldMapping(env_var="FIELD1", default="default1", required=False, description="Field 1")
                }

        class Plugin2(JiraPlugin):
            @property
            def command_name(self):
                return "plugin2"

            @property
            def help_text(self):
                return "Plugin 2"

            def register_arguments(self, parser):
                pass

            def execute(self, client, args):
                return True

            def rest_operation(self, client, **kwargs):
                return {}

            def get_field_mappings(self):
                return {
                    "field2": FieldMapping(env_var="FIELD2", default="default2", required=True, description="Field 2")
                }

        registry = PluginRegistry()

        for plugin_class in [Plugin1, Plugin2]:
            plugin = plugin_class()
            command_name = plugin.command_name
            registry._plugins[command_name] = plugin
            field_mappings = plugin.get_field_mappings()
            if field_mappings:
                registry._field_mappings[command_name] = field_mappings

        # Verify all field mappings are accessible
        all_mappings = registry.get_all_field_mappings()
        assert len(all_mappings) == 2
        assert "plugin1" in all_mappings
        assert "plugin2" in all_mappings
        assert all_mappings["plugin1"]["field1"].env_var == "FIELD1"
        assert all_mappings["plugin2"]["field2"].env_var == "FIELD2"

    def test_clear_removes_field_mappings(self):
        """Test that clear() removes all field mappings."""
        registry = PluginRegistry()
        registry._field_mappings["test"] = {"field": FieldMapping(env_var="TEST", description="Test field")}

        assert len(registry.get_all_field_mappings()) == 1

        registry.clear()

        assert registry.get_all_field_mappings() == {}

    def test_create_issue_plugin_has_field_mappings(self):
        """Test that CreateIssuePlugin registers field mappings."""
        plugin = CreateIssuePlugin()
        mappings = plugin.get_field_mappings()

        # Verify field mappings for epic and story points
        assert "epic" in mappings
        assert "story_points" in mappings
        assert mappings["epic"].env_var == "JIRA_EPIC_FIELD"
        assert mappings["story_points"].env_var == "JIRA_STORY_POINTS_FIELD"
