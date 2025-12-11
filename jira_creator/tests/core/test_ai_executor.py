#!/usr/bin/env python
"""
Unit tests for AIExecutor class.

Tests the AI-powered command execution functionality including JSON extraction
from various AI response formats.
"""

import json
from unittest.mock import MagicMock, patch

from jira_creator.core.ai_executor import AIExecutor


class TestAIExecutorJsonExtraction:
    """Test JSON extraction from AI responses in various formats."""

    def test_extract_json_from_markdown_json_block(self):
        """Test extracting JSON from ```json code block."""
        content = """```json
[
    {
        "function": "set_priority",
        "args": {"issue_key": "AAP-123", "priority": "Medium"},
        "action": "Set priority to Medium"
    }
]
```"""
        result = AIExecutor.extract_json_from_response(content)
        # Verify it's valid JSON and contains the expected data
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["function"] == "set_priority"
        assert parsed[0]["args"]["issue_key"] == "AAP-123"
        assert parsed[0]["args"]["priority"] == "Medium"

    def test_extract_json_from_generic_code_block(self):
        """Test extracting JSON from generic ``` code block."""
        content = """Here's the fix:
```
[{"function": "set_priority", "args": {"issue_key": "AAP-123", "priority": "High"}}]
```
This should work."""
        result = AIExecutor.extract_json_from_response(content)
        assert "[" in result and "]" in result
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["function"] == "set_priority"

    def test_extract_json_from_plain_array(self):
        """Test extracting plain JSON array without code blocks."""
        content = '[{"function": "set_priority", "args": {"issue_key": "AAP-123", "priority": "Low"}}]'
        result = AIExecutor.extract_json_from_response(content)
        assert result == content
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 1

    def test_extract_json_from_plain_object(self):
        """Test extracting plain JSON object without code blocks."""
        content = '{"function": "set_priority", "args": {"issue_key": "AAP-123"}}'
        result = AIExecutor.extract_json_from_response(content)
        assert result == content
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed["function"] == "set_priority"

    def test_extract_json_with_text_before(self):
        """Test extracting JSON when there's explanatory text before."""
        content = """I'll help you fix this issue.

[{"function": "set_priority", "args": {"issue_key": "AAP-123", "priority": "Medium"}}]"""
        result = AIExecutor.extract_json_from_response(content)
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 1

    def test_extract_json_with_text_after(self):
        """Test extracting JSON when there's explanatory text after."""
        content = """[{"function": "set_priority", "args": {"issue_key": "AAP-123", "priority": "High"}}]

This fix will set the priority correctly."""
        result = AIExecutor.extract_json_from_response(content)
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 1

    def test_extract_empty_json_array(self):
        """Test extracting empty JSON array."""
        content = "```json\n[]\n```"
        result = AIExecutor.extract_json_from_response(content)
        assert result == "[]"
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == []

    def test_extract_empty_json_object(self):
        """Test extracting empty JSON object."""
        content = "```json\n{}\n```"
        result = AIExecutor.extract_json_from_response(content)
        assert result == "{}"
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == {}

    def test_extract_nested_json(self):
        """Test extracting nested JSON structures."""
        content = """```json
{
    "fixes": [
        {"function": "set_priority", "args": {"issue_key": "AAP-123"}},
        {"function": "assign_issue", "args": {"issue_key": "AAP-123", "assignee": "user1"}}
    ]
}
```"""
        result = AIExecutor.extract_json_from_response(content)
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert "fixes" in parsed
        assert len(parsed["fixes"]) == 2

    def test_extract_json_with_whitespace(self):
        """Test extracting JSON with extra whitespace."""
        content = """

        ```json
        [{"function": "set_priority"}]
        ```

        """
        result = AIExecutor.extract_json_from_response(content)
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 1

    def test_extract_json_empty_string(self):
        """Test extracting from empty string."""
        result = AIExecutor.extract_json_from_response("")
        assert result == ""

    def test_extract_json_none(self):
        """Test extracting from None."""
        result = AIExecutor.extract_json_from_response(None)
        assert result == ""

    def test_extract_json_no_json_content(self):
        """Test extracting when there's no JSON in response."""
        content = "I couldn't generate any fixes for this issue."
        result = AIExecutor.extract_json_from_response(content)
        # Should return as-is since no JSON detected
        assert result == content

    def test_extract_json_with_explanation_in_markdown(self):
        """Test real-world case with explanation after JSON."""
        content = """```json
[]
```

**Explanation:**

Based on the available fix methods and the IMPORTANT RULES provided, no automated fixes can be applied to issue AAP-60384:

1. **❌ Issue has no assigned Epic** - Rule #2 explicitly states "Do NOT set epic links (epic assignment must be done manually)".
"""
        result = AIExecutor.extract_json_from_response(content)
        assert result == "[]"
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == []

    def test_extract_multiple_json_blocks_takes_first(self):
        """Test that only the first JSON block is extracted."""
        content = """```json
[{"function": "set_priority"}]
```

Here's an alternative:

```json
[{"function": "assign_issue"}]
```"""
        result = AIExecutor.extract_json_from_response(content)
        # Should get the first block
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["function"] == "set_priority"


class TestAIExecutorInit:
    """Test AIExecutor initialization."""

    def test_init(self):
        """Test AIExecutor initialization."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        executor = AIExecutor(client, plugin_registry, ai_provider)

        assert executor.client == client
        assert executor.plugin_registry == plugin_registry
        assert executor.ai_provider == ai_provider
        assert executor._fix_registry is None


class TestAIExecutorFixRegistry:
    """Test fix registry building and management."""

    def test_fix_registry_builds_from_plugins(self):
        """Test that fix_registry property builds registry from all plugins - covers lines 124-156."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        # Mock plugin with fix capabilities
        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {
                "method_name": "test_fix_method",
                "description": "Test fix",
                "params": {"issue_key": "str"},
                "conditions": {"required_status": ["Open"]},
            }
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        # Access the property
        registry = executor.fix_registry

        # Verify registry was built
        assert "test_fix_method" in registry
        assert registry["test_fix_method"]["description"] == "Test fix"
        assert registry["test_fix_method"]["_plugin"] == mock_plugin
        assert registry["test_fix_method"]["_plugin_name"] == "test-plugin"

    def test_fix_registry_caches_result(self):
        """Test that fix_registry caches the result - covers line 124-125."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        plugin_registry.get_all_plugin_names.return_value = []

        executor = AIExecutor(client, plugin_registry, ai_provider)

        # First access
        registry1 = executor.fix_registry

        # Second access should return same object
        registry2 = executor.fix_registry

        assert registry1 is registry2
        # get_all_plugin_names should only be called once due to caching
        assert plugin_registry.get_all_plugin_names.call_count == 1

    def test_fix_registry_skips_none_plugins(self):
        """Test that fix_registry skips None plugins - covers lines 133-134."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        plugin_registry.get_all_plugin_names.return_value = ["nonexistent-plugin"]
        plugin_registry.get_plugin.return_value = None

        executor = AIExecutor(client, plugin_registry, ai_provider)

        registry = executor.fix_registry

        # Should be empty since plugin was None
        assert len(registry) == 0

    def test_fix_registry_handles_no_fix_capabilities(self):
        """Test fix_registry handles plugins without fix capabilities - covers lines 137-141."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        # Mock plugin that raises NotImplementedError
        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.side_effect = NotImplementedError()

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        registry = executor.fix_registry

        # Should be empty since plugin doesn't implement fix capabilities
        assert len(registry) == 0

    def test_fix_registry_handles_attribute_error(self):
        """Test fix_registry handles plugins missing get_fix_capabilities - covers lines 137-141."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        # Mock plugin that raises AttributeError
        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.side_effect = AttributeError()

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        registry = executor.fix_registry

        # Should be empty
        assert len(registry) == 0

    def test_get_available_methods_for_ai(self):
        """Test get_available_methods_for_ai formats methods for AI - covers lines 165-174."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {
                "method_name": "set_priority",
                "description": "Set issue priority",
                "params": {"issue_key": "str", "priority": "str"},
                "conditions": {"required_status": ["Open"]},
            }
        ]

        plugin_registry.get_all_plugin_names.return_value = ["priority-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        methods = executor.get_available_methods_for_ai()

        # Verify format
        assert "set_priority" in methods
        assert methods["set_priority"]["description"] == "Set issue priority"
        assert methods["set_priority"]["params"] == {"issue_key": "str", "priority": "str"}
        assert "applies_when" in methods["set_priority"]
        # Should NOT include _plugin or _plugin_name
        assert "_plugin" not in methods["set_priority"]

    def test_get_available_methods_for_ai_without_conditions(self):
        """Test get_available_methods_for_ai without conditions - covers lines 171-172."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "simple_fix", "description": "Simple fix", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["simple-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        methods = executor.get_available_methods_for_ai()

        # Should not have applies_when if no conditions
        assert "simple_fix" in methods
        assert "applies_when" not in methods["simple_fix"]


class TestAIExecutorGenerateFixes:
    """Test AI-powered fix generation."""

    def test_generate_fixes_success(self):
        """Test successful fix generation - covers lines 189-229."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {"issue_key": "str"}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        # Mock AI response
        ai_response = """```json
[
    {
        "function": "set_priority",
        "args": {"issue_key": "TEST-123", "priority": "High"},
        "action": "Set priority to High"
    }
]
```"""
        ai_provider.improve_text.return_value = ai_response

        executor = AIExecutor(client, plugin_registry, ai_provider)

        problems = ["Issue has no priority"]
        context = {"issue_status": "Open", "issue_type": "Bug"}

        with patch("jira_creator.core.ai_executor.TemplateLoader") as mock_template:
            mock_loader = MagicMock()
            mock_loader.get_template.return_value = "Fix this issue"
            mock_template.return_value = mock_loader

            fixes = executor.generate_fixes("TEST-123", problems, context)

        assert len(fixes) == 1
        assert fixes[0]["function"] == "set_priority"
        assert fixes[0]["args"]["priority"] == "High"

    def test_generate_fixes_no_methods_available(self):
        """Test generate_fixes when no methods available - covers lines 191-193."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        plugin_registry.get_all_plugin_names.return_value = []

        executor = AIExecutor(client, plugin_registry, ai_provider)

        fixes = executor.generate_fixes("TEST-123", ["problem"], {})

        assert fixes == []

    def test_generate_fixes_empty_ai_response(self):
        """Test generate_fixes with empty AI response - covers lines 211-214."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        # AI returns empty string
        ai_provider.improve_text.return_value = ""

        executor = AIExecutor(client, plugin_registry, ai_provider)

        with patch("jira_creator.core.ai_executor.TemplateLoader") as mock_template:
            mock_loader = MagicMock()
            mock_loader.get_template.return_value = "Fix this"
            mock_template.return_value = mock_loader

            with patch("builtins.print"):
                fixes = executor.generate_fixes("TEST-123", ["problem"], {})

        assert fixes == []

    def test_generate_fixes_no_json_extracted(self):
        """Test generate_fixes when JSON extraction returns empty - covers lines 220-223."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        # AI returns empty code block - extract_json_from_response will return whitespace
        ai_provider.improve_text.return_value = "```json\n   \n```"

        executor = AIExecutor(client, plugin_registry, ai_provider)

        with patch("jira_creator.core.ai_executor.TemplateLoader") as mock_template:
            mock_loader = MagicMock()
            mock_loader.get_template.return_value = "Fix this"
            mock_template.return_value = mock_loader

            with patch("builtins.print"):
                fixes = executor.generate_fixes("TEST-123", ["problem"], {})

        assert fixes == []

    def test_generate_fixes_json_decode_error(self):
        """Test generate_fixes with invalid JSON - covers lines 231-236."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        # AI returns invalid JSON
        ai_provider.improve_text.return_value = "[{invalid json}]"

        executor = AIExecutor(client, plugin_registry, ai_provider)

        with patch("jira_creator.core.ai_executor.TemplateLoader") as mock_template:
            mock_loader = MagicMock()
            mock_loader.get_template.return_value = "Fix this"
            mock_template.return_value = mock_loader

            with patch("builtins.print"):
                fixes = executor.generate_fixes("TEST-123", ["problem"], {})

        assert fixes == []

    def test_generate_fixes_general_exception(self):
        """Test generate_fixes with general exception - covers lines 238-241."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        # AI provider raises exception
        ai_provider.improve_text.side_effect = Exception("Test error")

        executor = AIExecutor(client, plugin_registry, ai_provider)

        with patch("jira_creator.core.ai_executor.TemplateLoader") as mock_template:
            mock_loader = MagicMock()
            mock_loader.get_template.return_value = "Fix this"
            mock_template.return_value = mock_loader

            with patch("builtins.print"):
                fixes = executor.generate_fixes("TEST-123", ["problem"], {})

        assert fixes == []

    def test_build_fix_prompt(self):
        """Test _build_fix_prompt builds correct prompt - covers lines 259-297."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        executor = AIExecutor(client, plugin_registry, ai_provider)

        problems = ["No priority set", "Missing assignee"]
        context = {
            "issue_status": "Open",
            "issue_type": "Bug",
            "active_sprint_name": "Sprint 10",
            "active_sprint_id": "123",
            "current_assignee": "john@example.com",
        }
        available_methods = {"set_priority": {"description": "Set priority", "params": {}}}

        with patch("jira_creator.core.ai_executor.TemplateLoader") as mock_template:
            mock_loader = MagicMock()
            mock_loader.get_template.return_value = "AI Helper Template"
            mock_template.return_value = mock_loader

            prompt = executor._build_fix_prompt("TEST-123", problems, context, available_methods)

        # Verify prompt contains expected elements
        assert "AI Helper Template" in prompt
        assert "TEST-123" in prompt
        assert "No priority set" in prompt
        assert "Missing assignee" in prompt
        assert "set_priority" in prompt
        assert "Sprint 10" in prompt
        assert "john@example.com" in prompt


class TestAIExecutorValidateFixes:
    """Test fix command validation."""

    def test_validate_fix_commands_unknown_method(self):
        """Test validation skips unknown methods - covers lines 317-320."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        plugin_registry.get_all_plugin_names.return_value = []

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "unknown_method", "args": {}}]
        context = {}

        with patch("builtins.print"):
            validated = executor._validate_fix_commands(commands, context)

        assert len(validated) == 0

    def test_validate_fix_commands_status_not_met(self):
        """Test validation skips when status condition not met - covers lines 329-339."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {
                "method_name": "test_fix",
                "description": "Test",
                "params": {},
                "conditions": {"required_status": ["In Progress"]},
            }
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "test_fix", "args": {}}]
        context = {"issue_status": "Open"}  # Different status

        with patch("builtins.print"):
            validated = executor._validate_fix_commands(commands, context)

        assert len(validated) == 0

    def test_validate_fix_commands_type_not_met(self):
        """Test validation skips when type condition not met - covers lines 342-352."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {
                "method_name": "test_fix",
                "description": "Test",
                "params": {},
                "conditions": {"required_type": ["Story"]},
            }
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "test_fix", "args": {}}]
        context = {"issue_type": "Bug"}  # Different type

        with patch("builtins.print"):
            validated = executor._validate_fix_commands(commands, context)

        assert len(validated) == 0

    def test_validate_fix_commands_all_conditions_met(self):
        """Test validation passes when all conditions met - covers line 354."""
        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {
                "method_name": "test_fix",
                "description": "Test",
                "params": {},
                "conditions": {"required_status": ["Open"], "required_type": ["Bug"]},
            }
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "test_fix", "args": {}}]
        context = {"issue_status": "Open", "issue_type": "Bug"}

        validated = executor._validate_fix_commands(commands, context)

        assert len(validated) == 1


class TestAIExecutorExecuteFixes:
    """Test fix execution."""

    def test_execute_fixes_success(self):
        """Test successful fix execution - covers lines 369-409."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]
        mock_plugin.execute_fix.return_value = True

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [
            {
                "function": "set_priority",
                "args": {"issue_key": "TEST-123", "priority": "High"},
                "action": "Set priority to High",
            }
        ]

        with patch("builtins.print"):
            success, failure = executor.execute_fixes(commands, interactive=False)

        assert success == 1
        assert failure == 0

    def test_execute_fixes_unknown_method(self):
        """Test execution with unknown method - covers lines 378-382."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        plugin_registry.get_all_plugin_names.return_value = []

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "unknown_method", "args": {}, "action": "Unknown"}]

        with patch("builtins.print"):
            success, failure = executor.execute_fixes(commands, interactive=False)

        assert success == 0
        assert failure == 1

    def test_execute_fixes_plugin_returns_false(self):
        """Test execution when plugin returns False - covers lines 410-413."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]
        mock_plugin.execute_fix.return_value = False

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "set_priority", "args": {}, "action": "Test"}]

        with patch("builtins.print"):
            success, failure = executor.execute_fixes(commands, interactive=False)

        assert success == 0
        assert failure == 1

    def test_execute_fixes_plugin_raises_exception(self):
        """Test execution when plugin raises exception - covers lines 415-419."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]
        mock_plugin.execute_fix.side_effect = Exception("Test error")

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "set_priority", "args": {}, "action": "Test"}]

        with patch("builtins.print"):
            success, failure = executor.execute_fixes(commands, interactive=False)

        assert success == 0
        assert failure == 1

    def test_execute_fixes_interactive_mode_accept(self):
        """Test interactive mode when user accepts - covers lines 388-396."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]
        mock_plugin.execute_fix.return_value = True

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "set_priority", "args": {}, "action": "Test"}]

        with patch("builtins.print"):
            with patch("builtins.input", return_value="y"):
                success, failure = executor.execute_fixes(commands, interactive=True)

        assert success == 1
        assert failure == 0

    def test_execute_fixes_interactive_mode_reject(self):
        """Test interactive mode when user rejects - covers lines 394-396."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "set_priority", "args": {}, "action": "Test"}]

        with patch("builtins.print"):
            with patch("builtins.input", return_value="n"):
                success, failure = executor.execute_fixes(commands, interactive=True)

        # Skipped, so 0 success and 0 failure
        assert success == 0
        assert failure == 0

    def test_execute_fixes_interactive_mode_keyboard_interrupt(self):
        """Test interactive mode with KeyboardInterrupt - covers lines 397-399."""

        client = MagicMock()
        plugin_registry = MagicMock()
        ai_provider = MagicMock()

        mock_plugin = MagicMock()
        mock_plugin.get_fix_capabilities.return_value = [
            {"method_name": "set_priority", "description": "Set priority", "params": {}}
        ]

        plugin_registry.get_all_plugin_names.return_value = ["test-plugin"]
        plugin_registry.get_plugin.return_value = mock_plugin

        executor = AIExecutor(client, plugin_registry, ai_provider)

        commands = [{"function": "set_priority", "args": {}, "action": "Test"}]

        with patch("builtins.print"):
            with patch("builtins.input", side_effect=KeyboardInterrupt()):
                success, failure = executor.execute_fixes(commands, interactive=True)

        # Interrupted, so 0 success and 0 failure
        assert success == 0
        assert failure == 0
