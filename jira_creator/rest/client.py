#!/usr/bin/env python
"""
Simplified JiraClient for the plugin architecture.

This client provides only the core methods needed by plugins:
- request() for HTTP calls
- A few high-level methods that plugins use
- Core properties like jira_url, build_payload
"""

import base64
import datetime
import difflib
import json
import os
import time
import traceback
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.exceptions.exceptions import AiError, JiraClientRequestError

logger = get_logger("client")

_PARSE_ERRORS = (ValueError, TypeError, AttributeError, KeyError)
_REQUEST_ERRORS = (RequestException, ValueError, TypeError, AttributeError, KeyError)
_AI_ERRORS = (AiError, RequestException, ValueError, TypeError, AttributeError, KeyError, RuntimeError, ImportError)
_APPLY_ERRORS = (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, SyntaxError)
_RELOAD_ERRORS = (ImportError, SyntaxError, AttributeError, OSError, TypeError, ValueError, RuntimeError)
_LOOKUP_ERRORS = (JiraClientRequestError, RequestException, ValueError, TypeError, AttributeError)

# No imports from rest/ops - plugins should implement their own REST logic


@dataclass
class ErrorContext:
    """Comprehensive error context for AI analysis."""

    http_method: str  # POST, GET, etc.
    api_path: str  # /rest/api/2/issue
    full_url: str  # Complete URL
    json_payload: dict[str, Any] | None
    query_params: dict[str, str] | None
    status_code: int  # 400, 401, 404, 500, etc.
    response_body: str  # Raw response text
    response_headers: dict[str, str]
    jira_error_messages: list[str]
    jira_field_errors: dict[str, str]
    timestamp: str
    jira_url: str
    project_key: str
    # JIRA API context for better AI analysis
    available_issue_types: list[str] | None = None
    custom_fields: dict[str, str] | None = None  # field_id -> field_name
    project_config: dict[str, Any] | None = None

    def to_json(self) -> str:
        """Serialize to JSON for AI analysis."""
        return json.dumps(asdict(self), indent=2)


@dataclass
class FileChange:
    """Represents a single file modification for auto-remediation."""

    file_path: str  # Absolute path to file
    old_content: str  # Current content (or section)
    new_content: str  # Proposed content
    line_start: int | None = None  # For partial file changes
    line_end: int | None = None


@dataclass
class FixProposal:
    """AI's structured fix proposal for auto-remediation."""

    analysis: str  # Markdown analysis (Phase 1 output)
    fix_type: str  # "codebase" | "payload" | "none"
    confidence: float  # 0.0-1.0 confidence in fix
    file_changes: list[FileChange]  # For codebase fixes
    payload_fix: dict[str, Any] | None  # For payload fixes
    reasoning: str  # Why this fix type chosen


class JiraClient:
    """
    Simplified Jira client for the plugin architecture.

    Provides core HTTP functionality and the specific high-level methods
    that plugins actually use.
    """

    def __init__(self, plugin_registry=None) -> None:
        """
        Initialize the Jira client with environment configuration.

        Arguments:
            plugin_registry: Optional PluginRegistry instance for plugin reloading after AI fixes
        """
        logger.debug("Initializing JiraClient")
        self.jira_url: str = EnvFetcher.get("JIRA_URL")
        self.project_key: str = EnvFetcher.get("JIRA_PROJECT_KEY")
        self.affects_version: str = EnvFetcher.get("JIRA_AFFECTS_VERSION")
        self.component_name: str = EnvFetcher.get("JIRA_COMPONENT_NAME")
        self.priority: str = EnvFetcher.get("JIRA_PRIORITY")
        self.jpat: str = EnvFetcher.get("JIRA_JPAT")
        self.jira_email: str = EnvFetcher.get("JIRA_EMAIL", default="")
        self.epic_field: str = EnvFetcher.get("JIRA_EPIC_FIELD")
        self.board_id: str = EnvFetcher.get("JIRA_BOARD_ID")
        self.fields_cache_path: str = os.path.expanduser("~/.config/rh-issue/fields.json")
        self.is_speaking: bool = False
        self.plugin_registry = plugin_registry  # For reloading plugins after AI fixes
        jira_host = (urlparse(self.jira_url).hostname or "").lower()
        self.is_cloud: bool = jira_host.endswith(".atlassian.net")
        api_version_override = EnvFetcher.get("JIRA_API_VERSION", default="")
        if api_version_override:
            self.api_version: str = api_version_override
        elif self.is_cloud:
            self.api_version = "3"
        else:
            self.api_version = "2"
        logger.debug(
            "JiraClient initialized for URL: %s (API v%s, cloud=%s)",
            self.jira_url,
            self.api_version,
            self.is_cloud,
        )

    def _build_auth_header(self) -> str:
        """Build the Authorization header value based on JIRA instance type.

        Cloud instances use Basic auth: base64(email:token).
        Data Center/Server instances use Bearer token auth.
        """
        if self.is_cloud and self.jira_email:
            credentials = base64.b64encode(f"{self.jira_email}:{self.jpat}".encode()).decode()
            return f"Basic {credentials}"
        return f"Bearer {self.jpat}"

    def _rewrite_api_path(self, path: str) -> str:
        """Rewrite API path to use the configured API version."""
        return path.replace("/rest/api/2/", f"/rest/api/{self.api_version}/")

    def _migrate_search_to_post(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None,
        json_data: dict[str, Any] | None,
    ) -> tuple:
        """Migrate deprecated GET /search to POST /search/jql.

        The /search endpoint is deprecated on both Cloud and Data Center.
        Returns (method, path, params, json_data) with search calls converted.
        """
        if method.upper() != "GET":
            return method, path, params, json_data

        # Handle query params embedded in path (e.g. /search?jql=...&maxResults=100)
        # Only match the issue search endpoint, not /user/search etc.
        search_path = path.split("?")[0].rstrip("/")
        if not (search_path.endswith("/search") and "/user/" not in search_path):
            return method, path, params, json_data

        # Parse query string params from path if present
        merged_params = dict(params) if params else {}
        if "?" in path:
            from urllib.parse import parse_qs

            parsed = urlparse(path)
            for key, values in parse_qs(parsed.query).items():
                merged_params[key] = values[0]

        # Convert to POST /search/jql with JSON body, always using API v3
        new_path = search_path.replace("/rest/api/2/search", "/rest/api/3/search") + "/jql"
        post_body: dict[str, Any] = {}
        if "jql" in merged_params:
            post_body["jql"] = merged_params["jql"]
        if "maxResults" in merged_params:
            post_body["maxResults"] = int(merged_params["maxResults"])
        if "fields" in merged_params:
            post_body["fields"] = [f.strip() for f in merged_params["fields"].split(",")]
        else:
            # v3 search/jql returns only 'id' by default; include essential fields
            post_body["fields"] = ["*all"]
        if "startAt" in merged_params:
            post_body["startAt"] = int(merged_params["startAt"])
        if "orderBy" in merged_params and "ORDER BY" not in post_body.get("jql", "").upper():
            post_body["jql"] = post_body.get("jql", "") + f" ORDER BY {merged_params['orderBy']}"

        logger.debug("Migrated GET %s to POST %s", path, new_path)
        return "POST", new_path, None, post_body

    # jscpd:ignore-start
    def generate_curl_command(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        # jscpd:ignore-end
        """Generate a curl command for debugging HTTP requests."""
        parts = [f"curl -X {method.upper()}"]

        for k, v in headers.items():
            safe_value = v
            parts.append(f"-H '{k}: {safe_value}'")

        if json_data:
            body = json.dumps(json_data)
            parts.append(f"--data '{body}'")

        if params:
            from urllib.parse import urlencode

            url += "?" + urlencode(params)

        parts.append(f"'{url}'")
        command = " \\\n  ".join(parts)
        command = command + "\n"

        print("\n🔧 You can debug with this curl command:\n" + command)

    # jscpd:ignore-start
    def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> tuple[int, dict[str, Any]]:
        # jscpd:ignore-end
        """Send a HTTP request and return status code and response data."""
        logger.debug("HTTP %s request to %s", method, url)
        logger.debug("Request params: %s, has_json_data: %s", params, json_data is not None)

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=timeout,
            )
            logger.debug("Response status code: %s", response.status_code)

            # Handle error responses
            if response.status_code >= 400:
                logger.warning("HTTP error %s for %s %s", response.status_code, method, url)
                self.print_error_message(response)
                # Preserve raw response and headers for AI analysis
                return response.status_code, {
                    "_raw_response": response.text,
                    "_response_headers": dict(response.headers),
                }

            # Handle empty responses
            if not response.content.strip():
                logger.debug("Empty response received")
                return response.status_code, {}

            # Parse JSON response
            try:
                result = response.json()
                logger.debug("Successfully parsed JSON response")
                return response.status_code, result
            except ValueError:
                logger.error("Failed to parse JSON response")
                print("❌ Could not parse JSON. Raw response:")
                traceback.print_exc()
                return response.status_code, {}

        except RequestException as e:
            logger.error("Request exception: %s", e)
            print(f"⚠️ Request error: {e}")
            raise JiraClientRequestError(e) from e

    def print_error_message(self, response) -> None:
        """Print formatted error message from HTTP response."""
        status_code = response.status_code

        # Handle specific status codes
        if status_code == 404:
            print("❌ Resource not found")
            return
        if status_code == 401:
            print("❌ Unauthorized access")
            return

        # Try to extract detailed error information
        error_detail = self.extract_error_detail(response)
        if error_detail:
            print(f"❌ Client/Server error ({status_code}): {error_detail}")
        else:
            print(f"❌ Client/Server error: {status_code}")

    def extract_error_detail(self, response) -> str:
        """Extract error detail from response JSON."""
        try:
            error_data = response.json()
            if error_data.get("errorMessages"):
                return "; ".join(error_data["errorMessages"])
            if error_data.get("errors"):
                error_msgs = [f"{field}: {msg}" for field, msg in error_data["errors"].items()]
                return "; ".join(error_msgs)
            if "message" in error_data:
                return error_data["message"]
        except _PARSE_ERRORS:
            # If we can't parse the error, use the raw text
            return response.text[:200] if response.text else ""
        return ""

    def fetch_jira_context_for_error(
        self,
    ) -> tuple[list[str] | None, dict[str, str] | None, dict[str, Any] | None]:
        """
        Fetch JIRA API metadata to provide context for AI error analysis.

        Returns:
            Tuple of (issue_types, custom_fields, project_config)
            Returns (None, None, None) if fetch fails
        """
        try:
            logger.debug("Fetching JIRA API metadata for error context...")

            headers = {
                "Authorization": self._build_auth_header(),
                "Content-Type": "application/json",
            }

            issue_types = None
            custom_fields = None
            project_config = None

            # Fetch issue types (quick, helpful for create/update errors)
            try:
                response = requests.get(
                    self._rewrite_api_path(f"{self.jira_url}/rest/api/2/issuetype"),
                    headers=headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    types_data = response.json()
                    issue_types = [t.get("name") for t in types_data if "name" in t]
                    logger.debug("Fetched %d issue types", len(issue_types))
            except _REQUEST_ERRORS as e:
                logger.debug("Failed to fetch issue types: %s", e)

            # Fetch custom fields (crucial for field ID errors)
            try:
                response = requests.get(
                    self._rewrite_api_path(f"{self.jira_url}/rest/api/2/field"),
                    headers=headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    fields_data = response.json()
                    custom_fields = {
                        f.get("id"): f.get("name")
                        for f in fields_data
                        if f.get("custom") and f.get("id") and f.get("name")
                    }
                    logger.debug("Fetched %d custom fields", len(custom_fields))
            except _REQUEST_ERRORS as e:
                logger.debug("Failed to fetch custom fields: %s", e)

            # Fetch project config (if project key available)
            if self.project_key:
                try:
                    response = requests.get(
                        self._rewrite_api_path(f"{self.jira_url}/rest/api/2/project/{self.project_key}"),
                        headers=headers,
                        timeout=5,
                    )
                    if response.status_code == 200:
                        project_config = response.json()
                        logger.debug("Fetched project config for: %s", self.project_key)
                except _REQUEST_ERRORS as e:
                    logger.debug("Failed to fetch project config: %s", e)

            return issue_types, custom_fields, project_config

        except _REQUEST_ERRORS as e:
            logger.warning("Failed to fetch JIRA context: %s", e)
            return None, None, None

    def analyze_error_with_ai(self, error_context: ErrorContext) -> str | None:
        """
        Analyze error using AI provider and return suggestions.

        Arguments:
            error_context: Captured error details

        Returns:
            Formatted AI analysis or None if AI unavailable/fails
        """
        try:
            # Check if AI provider is configured
            ai_provider_name = EnvFetcher.get("JIRA_AI_PROVIDER", default="")
            if not ai_provider_name:
                logger.debug("AI provider not configured, skipping error analysis")
                return None

            # Get AI provider
            # pylint: disable=import-outside-toplevel
            from jira_creator.providers import get_ai_provider
            from jira_creator.rest.prompts import PromptLibrary

            ai_provider = get_ai_provider(ai_provider_name)

            # Get error analysis prompt
            prompt = PromptLibrary.get_error_analysis_prompt()

            # Analyze error
            logger.info("Requesting AI analysis of error...")
            analysis = ai_provider.analyze_error(prompt, error_context.to_json())

            logger.debug("AI analysis completed successfully")
            return analysis

        except _AI_ERRORS as e:
            # AI analysis is optional - don't fail if it errors
            logger.warning("AI error analysis failed: %s", e)
            return None

    def show_diff(self, old_content: str, new_content: str, file_path: str = "file") -> None:
        """
        Display unified diff between old and new content.

        Arguments:
            old_content: Original content
            new_content: New content
            file_path: File path for diff header
        """
        diff_lines = list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"{file_path} (original)",
                tofile=f"{file_path} (fixed)",
                lineterm="",
            )
        )

        if diff_lines:
            print("\n📊 Diff:")
            for line in diff_lines:
                print(line.rstrip())
        else:
            print("\n📊 No differences to show")

    def analyze_and_fix_error(self, error_context: ErrorContext) -> FixProposal | None:
        """
        Analyze error and return structured fix proposal.

        Arguments:
            error_context: Captured error details

        Returns:
            FixProposal object or None if AI unavailable/fails
        """
        try:
            # Check if AI provider is configured
            ai_provider_name = EnvFetcher.get("JIRA_AI_PROVIDER", default="")
            if not ai_provider_name:
                logger.debug("AI provider not configured, skipping auto-fix")
                return None

            # Get AI provider
            # pylint: disable=import-outside-toplevel
            from jira_creator.providers import get_ai_provider
            from jira_creator.rest.prompts import PromptLibrary

            ai_provider = get_ai_provider(ai_provider_name)

            # Get auto-fix prompt
            prompt = PromptLibrary.get_auto_fix_prompt()

            # Request structured fix from AI
            logger.info("Requesting AI auto-fix proposal...")
            json_response = ai_provider.analyze_and_fix_error(prompt, error_context.to_json())

            # Parse JSON response
            fix_data = json.loads(json_response)

            # Convert to FixProposal
            file_changes = [
                FileChange(
                    file_path=fc["file_path"],
                    old_content=fc["old_content"],
                    new_content=fc["new_content"],
                    line_start=fc.get("line_start"),
                    line_end=fc.get("line_end"),
                )
                for fc in fix_data.get("file_changes", [])
            ]

            fix_proposal = FixProposal(
                analysis=fix_data.get("analysis", ""),
                fix_type=fix_data.get("fix_type", "none"),
                confidence=fix_data.get("confidence", 0.0),
                file_changes=file_changes,
                payload_fix=fix_data.get("payload_fix"),
                reasoning=fix_data.get("reasoning", ""),
            )

            logger.debug("AI fix proposal generated successfully")
            return fix_proposal

        except _AI_ERRORS as e:
            # Auto-fix is optional - don't fail if it errors
            logger.warning("AI auto-fix failed: %s", e)
            return None

    def prompt_user_for_fix(self, fix_proposal: FixProposal) -> bool:
        """
        Display fix proposal and prompt user for consent.

        Arguments:
            fix_proposal: The proposed fix

        Returns:
            True if user accepts, False if user rejects
        """
        print(f"\n## Fix Type: {fix_proposal.fix_type.title()}")
        print(f"Confidence: {fix_proposal.confidence * 100:.0f}%")

        if fix_proposal.fix_type == "codebase" and fix_proposal.file_changes:
            print("\nFiles to modify:")
            for fc in fix_proposal.file_changes:
                print(f"  - {fc.file_path}")

            print("\n📝 Preview of changes:")
            for fc in fix_proposal.file_changes:
                # Show brief preview
                lines = fc.new_content.splitlines()
                preview_lines = lines[:3] if len(lines) > 3 else lines
                for line in preview_lines:
                    print(f"  {line}")
                if len(lines) > 3:
                    print(f"  ... ({len(lines) - 3} more lines)")

        elif fix_proposal.fix_type == "payload" and fix_proposal.payload_fix:
            print("\n📝 Payload changes:")
            print(json.dumps(fix_proposal.payload_fix, indent=2))

        # Prompt for user consent
        try:
            response = input("\n🔧 Apply this fix? (y/n/d for full diff): ").strip().lower()
            if response == "d" and fix_proposal.file_changes:
                # Show full diff
                for fc in fix_proposal.file_changes:
                    self.show_diff(fc.old_content, fc.new_content, fc.file_path)
                # Ask again
                response = input("\n🔧 Apply this fix? (y/n): ").strip().lower()

            return response == "y"
        except (KeyboardInterrupt, EOFError):
            print("\n\nFix cancelled by user")
            return False

    def apply_fix(self, fix_proposal: FixProposal) -> bool:
        """
        Apply the proposed fix (codebase or payload).

        Arguments:
            fix_proposal: The fix to apply

        Returns:
            True if successful, False if failed
        """
        if fix_proposal.fix_type == "codebase":
            return self.apply_codebase_fix(fix_proposal.file_changes)
        if fix_proposal.fix_type == "payload":
            # Payload fix doesn't need to be "applied" here - it's handled in request() retry
            logger.info("Payload fix will be applied on retry")
            return True
        logger.warning("Fix type 'none' - no fix to apply")
        return False

    def apply_codebase_fix(self, file_changes: list[FileChange]) -> bool:
        """
        Apply codebase fixes by modifying files.

        Arguments:
            file_changes: List of file changes to apply

        Returns:
            True if all changes applied successfully, False otherwise
        """
        modified_python_files = []
        modified_env_fetcher = False

        try:
            for fc in file_changes:
                # Validate file exists
                if not os.path.exists(fc.file_path):
                    logger.error("File does not exist: %s", fc.file_path)
                    print(f"❌ File does not exist: {fc.file_path}")
                    return False

                # Read current content
                with open(fc.file_path, "r", encoding="utf-8") as f:
                    current_content = f.read()

                # Verify old_content matches
                if fc.old_content not in current_content:
                    logger.error("Old content not found in file: %s", fc.file_path)
                    print(f"❌ Old content not found in file: {fc.file_path}")
                    print("File may have changed since error analysis")
                    return False

                # Apply fix
                new_content = current_content.replace(fc.old_content, fc.new_content)

                # Write fixed content
                with open(fc.file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                logger.info("Applied fix to: %s", fc.file_path)
                print(f"✅ Modified: {fc.file_path}")

                # Show diff
                self.show_diff(fc.old_content, fc.new_content, fc.file_path)

                # Track Python files for reloading
                if fc.file_path.endswith(".py"):
                    modified_python_files.append(fc.file_path)
                    # Special tracking for env_fetcher.py
                    if "env_fetcher.py" in fc.file_path:
                        modified_env_fetcher = True

            # Reload all modified Python modules
            if modified_python_files:
                self._reload_modified_modules(modified_python_files, modified_env_fetcher)

            return True

        except _APPLY_ERRORS as e:
            logger.error("Failed to apply codebase fix: %s", e)
            print(f"❌ Failed to apply fix: {e}")
            return False

    def _reload_modified_modules(self, modified_files: list[str], env_fetcher_modified: bool) -> None:
        """
        Reload all modified Python modules to apply changes immediately.

        Arguments:
            modified_files: List of absolute paths to modified .py files
            env_fetcher_modified: Whether env_fetcher.py was modified
        """
        import importlib
        import sys
        from pathlib import Path

        print("\n🔄 Reloading modified modules...")

        # Special handling for env_fetcher.py
        if env_fetcher_modified:
            print("\n⚠️  IMPORTANT: env_fetcher.py was modified!")
            print("   If DEFAULT_VALUES were changed, you need to update your environment variables:")
            print("   - Set the appropriate JIRA_* environment variables")
            print("   - Or restart your shell to use the new defaults")
            print("   - EnvFetcher.get() will use environment variables if set\n")

        reloaded_count = 0
        failed_count = 0

        for file_path in modified_files:
            try:
                # Convert file path to module name
                # e.g., /path/to/jira_creator/plugins/create_issue_plugin.py -> jira_creator.plugins.create_issue_plugin
                file_path_obj = Path(file_path)

                # Find the jira_creator part of the path
                parts = file_path_obj.parts
                module_name = None
                try:
                    jira_creator_idx = parts.index("jira_creator")
                    # Exclude the .py file, then append the module stem.
                    module_parts = list(parts[jira_creator_idx:-1]) + [file_path_obj.stem]
                    module_name = ".".join(module_parts)
                except ValueError:
                    # File is not in jira_creator package (e.g., external plugin)
                    logger.debug("File not in jira_creator package: %s", file_path)

                # Reload the module if we found a module name
                if module_name and module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    logger.info("Reloaded module: %s", module_name)
                    print(f"  ✅ Reloaded: {module_name}")
                    reloaded_count += 1
                elif module_name:
                    logger.debug("Module not yet loaded, skipping reload: %s", module_name)
                    print(f"  ℹ️  Not loaded yet: {module_name} (will be loaded on next import)")

                # If this is a plugin, also reload it in the registry (regardless of module path)
                if file_path.endswith("_plugin.py") and self.plugin_registry:
                    if self.plugin_registry.reload_plugin_from_file(file_path):
                        logger.info("Re-registered plugin from: %s", file_path)
                        print(f"  ✅ Re-registered plugin: {os.path.basename(file_path)}")
                        reloaded_count += 1
                    else:
                        logger.warning("Failed to re-register plugin: %s", file_path)
                        print(f"  ⚠️  Failed to re-register plugin: {os.path.basename(file_path)}")
                        failed_count += 1

            except _RELOAD_ERRORS as e:
                logger.warning("Failed to reload %s: %s", file_path, e)
                print(f"  ⚠️  Failed to reload: {os.path.basename(file_path)}")
                failed_count += 1

        # Summary
        if reloaded_count > 0:
            print(f"\n✅ Successfully reloaded {reloaded_count} module(s)")
        if failed_count > 0:
            print(f"⚠️  {failed_count} module(s) failed to reload - you may need to restart")

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        debug: bool = False,
        timeout: int = 10,
    ) -> dict[str, Any] | None:
        """
        Perform HTTP request to Jira API with retry logic.

        This is the core method that plugins use for all HTTP calls.
        """
        path = self._rewrite_api_path(path)
        method, path, params, json_data = self._migrate_search_to_post(method, path, params, json_data)
        logger.info("Jira API request: %s %s", method, path)
        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": self._build_auth_header(),
            "Content-Type": "application/json",
        }

        retries = 3
        delay = 2

        for attempt in range(retries):
            logger.debug("Attempt %d of %d", attempt + 1, retries)
            status_code, result = self._request(
                method,
                url,
                headers,
                json_data=json_data,
                params=params,
                timeout=timeout,
            )

            if debug:
                self.generate_curl_command(method, url, headers, json_data=json_data, params=params)

            if 200 <= status_code < 300:
                logger.info("Request successful: %s %s (status %s)", method, path, status_code)
                return result

            if attempt < retries - 1:
                logger.warning("Attempt %d: Sleeping %ds before retry...", attempt + 1, delay)
                print(f"Attempt {attempt + 1}: Sleeping before retry...")
                time.sleep(delay)

        # All retries failed - capture error context and analyze
        logger.error(
            "Request failed after %d attempts: %s %s (status %s)",
            retries,
            method,
            path,
            status_code,
        )

        # Extract error details from the result
        jira_error_messages: list[str] = []
        jira_field_errors: dict[str, str] = {}
        response_body = result.get("_raw_response", "")
        response_headers = result.get("_response_headers", {})

        # Try to parse JIRA error messages from response body
        try:
            if response_body:
                error_data = json.loads(response_body)
                if "errorMessages" in error_data:
                    jira_error_messages = error_data["errorMessages"]
                if "errors" in error_data:
                    jira_field_errors = error_data["errors"]
        except (ValueError, TypeError) as e:
            logger.debug("Could not parse JIRA error body: %s", e)

        # Fetch JIRA API context for better AI analysis
        logger.info("Fetching JIRA API metadata to enhance error analysis...")
        issue_types, custom_fields, project_config = self.fetch_jira_context_for_error()

        # Create comprehensive error context
        error_context = ErrorContext(
            http_method=method,
            api_path=path,
            full_url=url,
            json_payload=json_data,
            query_params=params,
            status_code=status_code,
            response_body=response_body,
            response_headers=response_headers,
            jira_error_messages=jira_error_messages,
            jira_field_errors=jira_field_errors,
            timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
            jira_url=self.jira_url,
            project_key=self.project_key,
            available_issue_types=issue_types,
            custom_fields=custom_fields,
            project_config=project_config,
        )

        # Try Phase 2: AI auto-fix with user consent
        fix_proposal = self.analyze_and_fix_error(error_context)

        # pylint: disable=too-many-nested-blocks
        if fix_proposal and fix_proposal.fix_type != "none":
            # Display AI analysis
            print(f"\n🤖 AI Analysis:\n{fix_proposal.analysis}")

            # Prompt user for consent
            if self.prompt_user_for_fix(fix_proposal):
                # User accepted - apply the fix
                if self.apply_fix(fix_proposal):
                    print("\n✅ Fix applied!")

                    # Prepare for retry
                    retry_json_data = json_data

                    # If payload fix, merge with original payload
                    if fix_proposal.fix_type == "payload" and fix_proposal.payload_fix:
                        if retry_json_data is None:
                            retry_json_data = {}
                        # Deep merge payload_fix into json_data
                        for key, value in fix_proposal.payload_fix.items():
                            if isinstance(value, dict) and key in retry_json_data:
                                retry_json_data[key].update(value)
                            else:
                                retry_json_data[key] = value
                        logger.info("Merged payload fix into request")

                    # Retry the operation
                    print("\n🔄 Retrying operation with fix applied...")
                    retry_status, retry_result = self._request(
                        method,
                        url,
                        headers,
                        json_data=retry_json_data,
                        params=params,
                        timeout=timeout,
                    )

                    if 200 <= retry_status < 300:
                        print("✅ Success! Operation completed after applying fix.")
                        logger.info("Request succeeded after AI fix: %s %s", method, path)

                        # Suggest committing the change if codebase was modified
                        if fix_proposal.fix_type == "codebase":
                            print("\n💡 The AI fix resolved your issue. Consider committing the change:")
                            for fc in fix_proposal.file_changes:
                                print(f"   git add {fc.file_path}")
                            print('   git commit -m "Fix: AI-suggested fix for JIRA API error"')

                            # Check if non-plugin Python files were modified
                            plugin_files = [
                                fc for fc in fix_proposal.file_changes if fc.file_path.endswith("_plugin.py")
                            ]
                            other_python_files = [
                                fc
                                for fc in fix_proposal.file_changes
                                if fc.file_path.endswith(".py") and not fc.file_path.endswith("_plugin.py")
                            ]

                            if plugin_files and not other_python_files:
                                print("\n✅ Plugins were reloaded - changes are now active!")
                            elif other_python_files:
                                print("\n⚠️  Note: Non-plugin Python modules were modified. If the retry still fails,")
                                print("   you may need to restart the command to reload all modules.")
                                print("   Simply run your command again to reload the fixed code.")

                        return retry_result
                    # Retry failed even after fix
                    print(f"⚠️ Fix applied but operation still failing (status {retry_status})")
                    logger.warning(
                        "Request still failed after AI fix: %s %s (status %s)",
                        method,
                        path,
                        retry_status,
                    )
                    # Fall through to raise original error with suggestion
                else:
                    # Fix application failed
                    print("⚠️ Failed to apply fix")
                    logger.warning("Failed to apply AI fix")
                    # Fall through to raise error
            else:
                # User rejected fix
                print("Fix declined by user")
                logger.info("User declined AI fix")
                # Fall through to raise error

        # Fall back to Phase 1: Analysis only (if Phase 2 didn't work or wasn't available)
        if not fix_proposal or fix_proposal.fix_type == "none":
            ai_suggestion = self.analyze_error_with_ai(error_context)
        else:
            # We already have analysis from the fix proposal
            ai_suggestion = fix_proposal.analysis

        # Format error message (include Jira API details so callers can fix payloads)
        error_msg = f"Failed after {retries} attempts: Status Code {status_code}"
        if error_context.jira_error_messages:
            error_msg += "\n\nJira messages:\n" + "\n".join(error_context.jira_error_messages)
        if error_context.jira_field_errors:
            error_msg += "\n\nField errors:\n" + json.dumps(error_context.jira_field_errors, indent=2)
        if (
            not error_context.jira_error_messages
            and not error_context.jira_field_errors
            and error_context.response_body
        ):
            body_preview = error_context.response_body[:2000]
            error_msg += f"\n\nResponse body (preview):\n{body_preview}"
        if ai_suggestion:
            error_msg += f"\n\n🤖 AI Analysis:\n{ai_suggestion}"

        # Show debug info
        self.generate_curl_command(method, url, headers, json_data=json_data, params=params)
        print(f"Attempt {attempt + 1}: Final failure, raising error")

        raise JiraClientRequestError(error_msg)

    def get_field_name(self, field_id: str) -> str | None:
        """
        Get the human-readable name for a Jira field ID.

        Arguments:
            field_id: The field ID (e.g., "customfield_10001")

        Returns:
            The human-readable field name, or None if not found
        """
        logger.debug("Looking up field name for: %s", field_id)
        try:
            # Get all fields from JIRA (this endpoint returns all fields)
            response = self.request("GET", "/rest/api/2/field")
            if response and isinstance(response, list):
                # Find the field with matching ID
                for field in response:
                    if field.get("id") == field_id:
                        field_name = field.get("name")
                        logger.debug("Field %s maps to: %s", field_id, field_name)
                        return field_name
            logger.debug("Field %s not found", field_id)
        except _LOOKUP_ERRORS as e:
            # If field lookup fails, return None (will use original field_id)
            logger.warning("Failed to lookup field %s: %s", field_id, e)
        return None

    # build_payload has been removed - plugins should implement payload building directly

    # Note: Plugins should implement their own REST operations.
    # The above methods have been removed to force plugins to contain
    # both CLI and REST logic as per the plugin architecture design.
