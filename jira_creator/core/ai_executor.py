#!/usr/bin/env python
"""
AI-powered command executor for translating natural language to plugin calls.

This core service allows any plugin to leverage AI for executing complex operations
by translating problems into structured function calls based on plugin-registered
fix capabilities.
"""

import json
from typing import Any, Dict, List

from jira_creator.core.logger import get_logger
from jira_creator.templates.template_loader import TemplateLoader

logger = get_logger("ai_executor")


class AIExecutor:
    """Executes AI-generated commands via plugin-registered fix methods."""

    def __init__(self, client: Any, plugin_registry: Any, ai_provider: Any):
        """
        Initialize the AI executor.

        Arguments:
            client: JiraClient instance
            plugin_registry: PluginRegistry instance
            ai_provider: AI provider for generating fix commands
        """
        self.client = client
        self.plugin_registry = plugin_registry
        self.ai_provider = ai_provider
        self._fix_registry = None

    @staticmethod
    def _extract_from_markdown_block(content: str, marker: str) -> str:
        """Extract JSON from markdown code block with given marker."""
        if marker not in content:
            return ""
        start = content.find(marker)
        end = content.find("```", start + len(marker))
        if end != -1:
            json_content = content[start + len(marker) : end].strip()
            logger.debug("Extracted JSON from %s block: %s", marker, json_content[:100])
            return json_content
        return ""

    @staticmethod
    def _extract_balanced_json(content: str, start_idx: int, open_char: str, close_char: str) -> str:
        """Extract balanced JSON structure starting from given index."""
        depth = 0
        for i in range(start_idx, len(content)):
            if content[i] == open_char:
                depth += 1
            elif content[i] == close_char:
                depth -= 1
                if depth == 0:
                    json_content = content[start_idx : i + 1]
                    logger.debug("Extracted JSON %s: %s", open_char, json_content[:100])
                    return json_content
        return ""

    @staticmethod
    def extract_json_from_response(content: str) -> str:
        """
        Extract JSON from AI response, handling various formats.

        AI models may return JSON in different formats:
        - Wrapped in markdown code blocks: ```json ... ``` or ``` ... ```
        - With explanatory text before/after
        - Plain JSON

        Arguments:
            content: Raw AI response content

        Returns:
            Extracted JSON string
        """
        if not content or not content.strip():
            return ""

        content = content.strip()

        # Try to extract from markdown code blocks
        # Pattern 1: ```json ... ```
        result = AIExecutor._extract_from_markdown_block(content, "```json")
        if result:
            return result

        # Pattern 2: ``` ... ``` (generic code block)
        result = AIExecutor._extract_from_markdown_block(content, "```")
        if result:
            return result

        # Pattern 3: Look for [ or { at the start (plain JSON)
        json_start = -1
        for i, char in enumerate(content):
            if char in "[{":
                json_start = i
                break

        if json_start != -1:
            open_char = content[json_start]
            close_char = "]" if open_char == "[" else "}"
            result = AIExecutor._extract_balanced_json(content, json_start, open_char, close_char)
            if result:
                return result

        # No JSON found, return as-is
        logger.warning("Could not extract JSON from response, returning as-is")
        return content

    @property
    def fix_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Build fix method registry from all plugins.

        This property lazily builds and caches the registry of all fix
        capabilities registered by plugins.

        Returns:
            Dict mapping method_name to fix capability info + plugin reference
        """
        if self._fix_registry is not None:
            return self._fix_registry

        registry = {}

        # Query all plugins for their fix capabilities
        for plugin_name in self.plugin_registry.get_all_plugin_names():
            plugin = self.plugin_registry.get_plugin(plugin_name)

            if plugin is None:
                continue

            # Get fix capabilities from plugin
            try:
                capabilities = plugin.get_fix_capabilities()
            except (NotImplementedError, AttributeError):
                # Plugin doesn't implement fix capabilities
                continue

            # Register each capability
            for cap in capabilities:
                method_name = cap["method_name"]

                # Add plugin reference
                cap["_plugin"] = plugin
                cap["_plugin_name"] = plugin_name

                registry[method_name] = cap
                logger.debug("Registered fix method '%s' from plugin '%s'", method_name, plugin_name)

        logger.info("Built fix registry with %d methods from plugins", len(registry))
        self._fix_registry = registry
        return registry

    def get_available_methods_for_ai(self) -> Dict[str, Any]:
        """
        Get fix methods formatted for AI consumption.

        Returns:
            Dict of method_name -> description/params (without internal plugin refs)
        """
        ai_methods = {}

        for method_name, cap in self.fix_registry.items():
            ai_methods[method_name] = {"description": cap["description"], "params": cap["params"]}

            # Optionally include conditions as hints for AI
            if "conditions" in cap:
                ai_methods[method_name]["applies_when"] = cap["conditions"]

        return ai_methods

    def generate_fixes(self, issue_key: str, problems: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use AI to generate fix commands for lint problems.

        Arguments:
            issue_key: JIRA issue key
            problems: List of problem descriptions
            context: Dict with contextual info (status, type, active_sprint_id, etc.)

        Returns:
            List of fix commands in JSON format
        """
        # Get available methods for AI
        available_methods = self.get_available_methods_for_ai()

        if not available_methods:
            logger.warning("No fix methods available from plugins")
            return []

        # Build AI prompt
        prompt = self._build_fix_prompt(issue_key, problems, context, available_methods)
        logger.debug("AI fix prompt for %s (length: %d chars):\n%s", issue_key, len(prompt), prompt[:1000])

        # Get AI response
        try:
            logger.debug("Calling AI provider improve_text for %s", issue_key)
            content = self.ai_provider.improve_text(
                "You are a JIRA issue fixer that generates structured fix commands.", prompt
            )
            logger.debug(
                "AI provider returned content type: %s, value: %s", type(content), content[:200] if content else "None"
            )
            logger.debug("AI raw response for %s: %s", issue_key, content[:500])

            # Check if response is empty
            if not content or not content.strip():
                logger.error("AI returned empty response for %s", issue_key)
                print("⚠️  AI returned empty response")
                return []

            # Extract JSON from response (handles markdown code blocks, etc.)
            json_content = self.extract_json_from_response(content)

            if not json_content or not json_content.strip():
                logger.error("Failed to extract JSON from AI response for %s", issue_key)
                logger.error("AI response content: %s", content[:1000])
                print("⚠️  AI response did not contain valid JSON")
                return []

            # Parse and validate JSON response
            fix_commands = json.loads(json_content)
            validated = self._validate_fix_commands(fix_commands, context)
            logger.info("Generated %d validated fix commands for %s", len(validated), issue_key)
            return validated

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON for %s: %s", issue_key, e)
            logger.error("Extracted JSON content: %s", json_content[:1000] if "json_content" in locals() else "N/A")
            logger.error("Original AI response: %s", content[:1000] if "content" in locals() else "N/A")
            print(f"⚠️  Failed to parse AI response as JSON: {e}")
            print(f"⚠️  Extracted content: {json_content[:200] if 'json_content' in locals() else 'N/A'}")
            return []
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to generate fixes for %s: %s", issue_key, e)
            print(f"⚠️  Failed to generate fixes: {e}")
            return []

    def _build_fix_prompt(
        self, issue_key: str, problems: List[str], context: Dict[str, Any], available_methods: Dict[str, Any]
    ) -> str:
        """
        Build the AI prompt for generating fix commands.

        Arguments:
            issue_key: JIRA issue key
            problems: List of problems to fix
            context: Issue context
            available_methods: Available fix methods

        Returns:
            Formatted prompt string
        """
        # Load aihelper template
        template_loader = TemplateLoader(issue_type="aihelper")
        template = template_loader.get_template()

        # Build the prompt
        prompt = f"""{template}

Available fix methods:
{json.dumps(available_methods, indent=2)}

Context:
- Issue: {issue_key}
- Status: {context.get('issue_status', 'Unknown')}
- Type: {context.get('issue_type', 'Unknown')}
- Active Sprint: {context.get('active_sprint_name', 'None')}
- Active Sprint ID: {context.get('active_sprint_id', 'None')}
- Current Assignee: {context.get('current_assignee', 'Unassigned')}

Problems to fix:
{chr(10).join(f"- {p}" for p in problems)}

IMPORTANT RULES:
1. Only assign to sprint if status is "In Progress" AND active sprint is available
2. Do NOT set epic links (epic assignment must be done manually)
3. If status is "Refinement" and type is "Story", ensure acceptance criteria exists
4. Story points should NOT be set automatically (needs manual refinement)
5. Only use the available methods listed above
6. For each fix, provide a clear action description

Return a JSON array of fix commands. Example:
[
    {{
        "function": "set_priority",
        "args": {{"issue_key": "{issue_key}", "priority": "Medium"}},
        "action": "Set priority to Medium"
    }}
]
"""

        return prompt

    def _validate_fix_commands(
        self, fix_commands: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate AI-generated commands against plugin conditions.

        Arguments:
            fix_commands: List of command dicts from AI
            context: Issue context (status, type, etc.)

        Returns:
            Filtered list of valid commands
        """
        valid_commands = []

        for cmd in fix_commands:
            method_name = cmd.get("function")

            if method_name not in self.fix_registry:
                logger.warning("Unknown fix method from AI: %s", method_name)
                print(f"  ⚠️  Unknown fix method: {method_name}")
                continue

            cap = self.fix_registry[method_name]

            # Check conditions
            if "conditions" in cap:
                conditions = cap["conditions"]

                # Check required_status
                if "required_status" in conditions:
                    current_status = context.get("issue_status")
                    if current_status not in conditions["required_status"]:
                        logger.debug(
                            "Skipping %s: status '%s' not in required statuses %s",
                            method_name,
                            current_status,
                            conditions["required_status"],
                        )
                        print(f"  ⏭️  Skipping {method_name}: status '{current_status}' not applicable")
                        continue

                # Check required_type
                if "required_type" in conditions:
                    current_type = context.get("issue_type")
                    if current_type not in conditions["required_type"]:
                        logger.debug(
                            "Skipping %s: type '%s' not in required types %s",
                            method_name,
                            current_type,
                            conditions["required_type"],
                        )
                        print(f"  ⏭️  Skipping {method_name}: type '{current_type}' not applicable")
                        continue

            valid_commands.append(cmd)

        return valid_commands

    def execute_fixes(self, fix_commands: List[Dict[str, Any]], interactive: bool = False) -> tuple[int, int]:
        """
        Execute AI-generated fix commands via plugins.

        Arguments:
            fix_commands: List of command dicts from AI
            interactive: If True, ask user confirmation for each fix

        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0

        for cmd in fix_commands:
            method_name = cmd.get("function")
            args = cmd.get("args", {})
            action = cmd.get("action", "")

            # Get plugin that implements this method
            if method_name not in self.fix_registry:
                logger.error("Unknown fix method during execution: %s", method_name)
                print(f"  ❌ Unknown fix method: {method_name}")
                failure_count += 1
                continue

            cap = self.fix_registry[method_name]
            plugin = cap["_plugin"]

            # Interactive mode - ask for confirmation
            if interactive:
                print(f"\n  🤔 Proposed fix: {action}")
                print(f"     Method: {method_name}")
                print(f"     Args: {args}")
                try:
                    response = input("     Apply this fix? (y/n): ").strip().lower()
                    if response != "y":
                        print("     ⏭️  Skipped")
                        continue
                except (KeyboardInterrupt, EOFError):
                    print("\n     ⏭️  Skipped (interrupted)")
                    continue

            # Execute via plugin
            try:
                logger.debug("Executing %s with args %s", method_name, args)
                result = plugin.execute_fix(self.client, method_name, args)

                if result:
                    print(f"  ✅ {action}")
                    success_count += 1
                    logger.info("Successfully executed: %s", action)
                else:
                    print(f"  ❌ Failed: {action}")
                    failure_count += 1
                    logger.warning("Failed to execute: %s", action)

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error executing %s: %s", method_name, e)
                print(f"  ❌ Error executing {method_name}: {e}")
                failure_count += 1
                continue  # Skip and continue

        return success_count, failure_count
