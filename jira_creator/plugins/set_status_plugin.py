#!/usr/bin/env python
"""
Set status plugin for jira-creator.

This plugin implements the set-status command, allowing users to
change the status of Jira issues with support for transitions.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin


class SetStatusError(Exception):
    """Exception raised when setting status fails."""


class SetStatusPlugin(JiraPlugin):
    """Plugin for setting the status of Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "set-status"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Set the status of a Jira issue"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Modification"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ['set-status AAP-12345 "In Progress"', "set-status AAP-12345 Done"]

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "SetStatusError": SetStatusError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("status", help="The status to transition to")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the set-status command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            self.rest_operation(client, issue_key=args.issue_key, status=args.status)
            print(f"✅ Status set to '{args.status}'")

            # Handle special refinement status actions
            if args.status.lower() == "refinement":
                self._handle_refinement_status(client, args.issue_key)

            return True

        except SetStatusError as e:
            msg = f"❌ Failed to set status: {e}"
            print(msg)
            raise SetStatusError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:  # pylint: disable=too-many-locals
        """
        Perform the REST API operation to set status.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'status'

        Returns:
            Dict[str, Any]: Empty dict (transition endpoint returns no content)
        """
        issue_key = kwargs["issue_key"]
        status = kwargs["status"]

        # Get available transitions with field metadata (required fields for each transition)
        transitions = self._get_transitions_with_fields(client, issue_key)

        # Find matching transition
        transition_id = self._find_transition_id(transitions, status)

        if not transition_id:
            available = [t["name"] for t in transitions]
            raise SetStatusError(f"Status '{status}' not available. Available transitions: {', '.join(available)}")

        # Build payload: transition + any required fields for this transition
        path = f"/rest/api/2/issue/{issue_key}/transitions"
        payload = {"transition": {"id": transition_id}}

        transition_fields = self._get_required_fields_for_transition(transitions, transition_id)
        transition = next((t for t in transitions if str(t.get("id")) == str(transition_id)), None)
        has_transition_screen = bool(transition and transition.get("fields"))
        needs_issue_fields = bool(transition_fields or has_transition_screen or str(transition_id) == "61")
        issue_fields = {}
        if needs_issue_fields:
            # Workflow validators may require transition screen fields even when REST metadata marks
            # every field as required=false. Fetch issue data only for transitions that need it.
            issue_fields = client.request("GET", f"/rest/api/2/issue/{issue_key}").get("fields", {})

        if transition_fields:
            payload["fields"] = self._build_transition_fields(transition_fields, issue_fields)
        elif str(transition_id) == "61":
            payload["fields"] = {}
        else:
            if transition and transition.get("fields"):
                screen_fields = self._build_fields_from_transition_screen(transition, issue_fields, client)
                if screen_fields:
                    payload["fields"] = screen_fields

        # Closed transition (61) requires Workstream as an array
        workstream_field = EnvFetcher.get("JIRA_WORKSTREAM_FIELD", default="")

        if str(transition_id) == "61":
            if workstream_field:
                self._apply_workstream_field(payload, transitions, transition_id, issue_fields, workstream_field)
            # Workflow validator requires assignee — set to current user if unassigned
            if not issue_fields.get("assignee"):
                myself = client.request("GET", "/rest/api/2/myself")
                if client.is_cloud:
                    client.request(
                        "PUT",
                        f"/rest/api/2/issue/{issue_key}",
                        json_data={"fields": {"assignee": {"accountId": myself["accountId"]}}},
                    )
                else:
                    client.request(
                        "PUT",
                        f"/rest/api/2/issue/{issue_key}",
                        json_data={"fields": {"assignee": {"name": myself["name"]}}},
                    )

        return client.request("POST", path, json_data=payload)

    @staticmethod
    def _normalize_workstream(val: Any) -> List[Dict[str, Any]]:
        """Normalize Workstream to array of {id} as required by Jira."""
        if val is None or val == "":
            return []
        if isinstance(val, list) and val:
            return [{"id": x["id"]} if isinstance(x, dict) and x.get("id") else x for x in val]
        if isinstance(val, dict) and val.get("id"):
            return [{"id": val["id"]}]
        return [val] if val else []

    def _apply_workstream_field(self, payload, transitions, transition_id, issue_fields, workstream_field):
        """Apply workstream field for Closed transition (61)."""
        fields = payload.setdefault("fields", {})
        workstream = issue_fields.get(workstream_field)
        vals = self._normalize_workstream(workstream) if (workstream is not None and workstream != "") else []
        if not vals and workstream_field not in fields:
            vals = self._get_workstream_from_allowed(transitions, transition_id, workstream_field)
        if vals:
            fields[workstream_field] = vals

    def _get_workstream_from_allowed(self, transitions, transition_id, workstream_field):
        """Get workstream value from transition's allowed values."""
        for t in transitions:
            if str(t.get("id")) == str(transition_id):
                t_fields = t.get("fields") or {}
                meta = t_fields.get(workstream_field)
                if meta:
                    allowed = meta.get("allowedValues") or []
                    if allowed:
                        return self._normalize_workstream(allowed[0])
                break
        return []

    def _get_transitions(self, client: Any, issue_key: str) -> List[Dict[str, Any]]:
        """Get available transitions for an issue."""
        path = f"/rest/api/2/issue/{issue_key}/transitions"
        response = client.request("GET", path)
        return response.get("transitions", [])

    def _get_transitions_with_fields(self, client: Any, issue_key: str) -> List[Dict[str, Any]]:
        """Get available transitions with expand=transitions.fields to see required fields."""
        path = f"/rest/api/2/issue/{issue_key}/transitions"
        response = client.request("GET", path, params={"expand": "transitions.fields"})
        return response.get("transitions", [])

    def _get_required_fields_for_transition(
        self, transitions: List[Dict[str, Any]], transition_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Return required field id -> field meta for the given transition."""
        for t in transitions:
            if str(t.get("id")) == str(transition_id):
                fields = t.get("fields") or {}
                return {fid: meta for fid, meta in fields.items() if meta.get("required")}
        return {}

    def _build_transition_fields(
        self, transition_fields: Dict[str, Dict[str, Any]], issue_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build fields payload for transition: use issue's current value where present,
        otherwise use first allowedValue for the field if available.
        """
        out = {}
        for field_id, meta in transition_fields.items():
            current = issue_fields.get(field_id)
            if current is not None and current != "":
                # Use existing value; normalize to schema (id vs value) if needed
                schema = meta.get("schema", {})
                if schema.get("type") == "option" and isinstance(current, dict):
                    out[field_id] = {"id": current.get("id")} if current.get("id") else current
                elif schema.get("type") == "array" and isinstance(current, list) and current:
                    # e.g. multi-select: list of {id} or strings
                    out[field_id] = current
                else:
                    out[field_id] = current
                continue
            # No current value: use first allowedValue if present
            allowed = meta.get("allowedValues") or []
            if allowed:
                first = allowed[0]
                if isinstance(first, dict):
                    out[field_id] = {"id": first["id"]} if first.get("id") else first
                else:
                    out[field_id] = first
            # else: leave unset and let API return error with required field name
        return out

    def _build_fields_from_transition_screen(  # pylint: disable=too-many-branches
        self,
        transition: Dict[str, Any],
        issue_fields: Dict[str, Any],
        client: Any,
    ) -> Dict[str, Any]:
        """
        When transitions.fields marks nothing as required, Jira workflow may still require
        the transition screen to be submitted (assignee, description, custom fields, etc.).
        Copy current issue values for each field on the transition screen, defaulting
        assignee to the current user when unset.
        """
        out: Dict[str, Any] = {}
        screen = transition.get("fields") or {}
        # These appear on some transition screens but cannot be set via POST /transitions.
        skip_transition_fields = frozenset({"issuelinks", "subtasks", "attachment"})
        for field_id, meta in screen.items():
            if field_id in skip_transition_fields:
                continue
            # gh-sprint: API rejects copied values ("Sprint id must be a number"); sprint is set via board API.
            schema_custom = (meta.get("schema") or {}).get("custom", "")
            if isinstance(schema_custom, str) and schema_custom.endswith("gh-sprint"):
                continue
            current = issue_fields.get(field_id)
            if field_id == "assignee":
                if current and isinstance(current, dict) and (current.get("accountId") or current.get("name")):
                    if client.is_cloud and current.get("accountId"):
                        out[field_id] = {"accountId": current["accountId"]}
                    elif not client.is_cloud and current.get("name"):
                        out[field_id] = {"name": current["name"]}
                    else:
                        out[field_id] = current
                else:
                    myself = client.request("GET", "/rest/api/2/myself")
                    if client.is_cloud:
                        out[field_id] = {"accountId": myself["accountId"]}
                    else:
                        out[field_id] = {"name": myself["name"]}
                continue

            if current is None or current == "":
                continue
            if isinstance(current, list) and len(current) == 0:
                continue
            if isinstance(current, dict) and not current:
                continue

            schema = meta.get("schema", {})
            stype = schema.get("type")
            if field_id == "priority" and isinstance(current, dict) and current.get("id"):
                out[field_id] = {"id": current["id"]}
            elif stype == "option" and isinstance(current, dict):
                out[field_id] = {"id": current["id"]} if current.get("id") else current
            elif stype == "array" and isinstance(current, list) and current:
                if isinstance(current[0], dict) and current[0].get("id"):
                    out[field_id] = [{"id": x["id"]} for x in current if isinstance(x, dict) and x.get("id")]
                else:
                    out[field_id] = current
            else:
                out[field_id] = current
        return out

    def _find_transition_id(self, transitions: List[Dict], status: str) -> Optional[str]:
        """Find transition ID for the given status name."""
        status_lower = status.lower()

        for transition in transitions:
            if transition["name"].lower() == status_lower:
                return transition["id"]

        return None

    def _handle_refinement_status(self, client: Any, issue_key: str) -> None:
        """Handle special actions for refinement status."""
        try:
            # Move to top of backlog
            print("📌 Moving issue to top of backlog...")
            client.request(
                "PUT",
                "/rest/greenhopper/1.0/sprint/rank",
                json_data={"issueToMove": issue_key, "moveToTop": True},
            )

            # Get issue details to find epic
            issue_details = client.request("GET", f"/rest/api/2/issue/{issue_key}")
            epic_key = issue_details.get("fields", {}).get("parent", {}).get("key")

            if epic_key:
                # Move to top of epic
                print(f"📌 Moving issue to top of epic {epic_key}...")
                client.request(
                    "PUT",
                    "/rest/greenhopper/1.0/rank/global/first",
                    json_data={"issueToMove": issue_key, "parentKey": epic_key},
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Don't fail the whole operation if ranking fails
            print(f"⚠️  Could not complete ranking operations: {e}")
