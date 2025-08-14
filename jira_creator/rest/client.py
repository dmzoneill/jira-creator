#!/usr/bin/env python
"""
Simplified JiraClient for the plugin architecture.

This client provides only the core methods needed by plugins:
- request() for HTTP calls
- A few high-level methods that plugins use
- Core properties like jira_url, build_payload
"""

import json
import os
import time
import traceback
from typing import Any, Dict, Optional, Tuple

import requests
from requests.exceptions import RequestException

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import JiraClientRequestError

# No imports from rest/ops - plugins should implement their own REST logic


class JiraClient:
    """
    Simplified Jira client for the plugin architecture.

    Provides core HTTP functionality and the specific high-level methods
    that plugins actually use.
    """

    def __init__(self) -> None:
        """Initialize the Jira client with environment configuration."""
        self.jira_url: str = EnvFetcher.get("JIRA_URL")
        self.project_key: str = EnvFetcher.get("JIRA_PROJECT_KEY")
        self.affects_version: str = EnvFetcher.get("JIRA_AFFECTS_VERSION")
        self.component_name: str = EnvFetcher.get("JIRA_COMPONENT_NAME")
        self.priority: str = EnvFetcher.get("JIRA_PRIORITY")
        self.jpat: str = EnvFetcher.get("JIRA_JPAT")
        self.epic_field: str = EnvFetcher.get("JIRA_EPIC_FIELD")
        self.board_id: str = EnvFetcher.get("JIRA_BOARD_ID")
        self.fields_cache_path: str = os.path.expanduser("~/.config/rh-issue/fields.json")
        self.is_speaking: bool = False

    # jscpd:ignore-start
    def generate_curl_command(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
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
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        # jscpd:ignore-end
        """Send a HTTP request and return status code and response data."""
        try:
            response = requests.request(method, url, headers=headers, json=json_data, params=params, timeout=10)
            if response.status_code == 404:
                print("❌ Resource not found")
                return response.status_code, {}

            if response.status_code == 401:
                print("❌ Unauthorized access")
                return response.status_code, {}

            if response.status_code >= 400:
                print(f"❌ Client/Server error: {response.status_code}")
                return response.status_code, {}

            if not response.content.strip():
                return response.status_code, {}

            try:
                result = response.json()
                return response.status_code, result
            except ValueError:
                print("❌ Could not parse JSON. Raw response:")
                traceback.print_exc()
                return response.status_code, {}

        except RequestException as e:
            print(f"⚠️ Request error: {e}")
            raise JiraClientRequestError(e) from e

    def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        debug: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Perform HTTP request to Jira API with retry logic.

        This is the core method that plugins use for all HTTP calls.
        """
        url = f"{self.jira_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.jpat}",
            "Content-Type": "application/json",
        }

        retries = 3
        delay = 2

        for attempt in range(retries):
            status_code, result = self._request(method, url, headers, json_data=json_data, params=params)

            if debug:
                self.generate_curl_command(method, url, headers, json_data=json_data, params=params)

            if 200 <= status_code < 300:
                return result

            if attempt < retries - 1:
                print(f"Attempt {attempt + 1}: Sleeping before retry...")
                time.sleep(delay)

        self.generate_curl_command(method, url, headers, json_data=json_data, params=params)
        print(f"Attempt {attempt + 1}: Final failure, raising error")
        raise JiraClientRequestError(f"Failed after {retries} attempts: Status Code {status_code}")

    def get_field_name(self, field_id: str) -> Optional[str]:
        """
        Get the human-readable name for a Jira field ID.

        Arguments:
            field_id: The field ID (e.g., "customfield_10001")

        Returns:
            The human-readable field name, or None if not found
        """
        try:
            # Get all fields from JIRA (this endpoint returns all fields)
            response = self.request("GET", "/rest/api/2/field")
            if response and isinstance(response, list):
                # Find the field with matching ID
                for field in response:
                    if field.get("id") == field_id:
                        return field.get("name")
        except Exception:  # pylint: disable=broad-exception-caught
            # If field lookup fails, return None (will use original field_id)
            pass
        return None

    # build_payload has been removed - plugins should implement payload building directly

    # Note: Plugins should implement their own REST operations.
    # The above methods have been removed to force plugins to contain
    # both CLI and REST logic as per the plugin architecture design.
