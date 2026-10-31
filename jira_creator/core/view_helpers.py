"""
This module provides functionality to interact with JIRA issues, including fetching view columns, sorting, filtering,
and formatting issue data for display.

Functions:
- fetch_view_columns: Retrieves view columns from the environment or returns None. If any column contains 'JIRA', it
fetches the corresponding environment variable.
- get_sorted_columns: Parses a sorting string to return a list of tuples containing column names and their sort order.
- filter_columns: Filters issue data based on specified view columns.
- sort_rows: Sorts a list of rows based on specified sort columns and their order.
- format_and_print_rows: Formats and prints rows of issue data, adjusting for column widths and ensuring proper
alignment.
- flatten_fields: Flattens the fields dictionary in a JIRA issue into the parent dictionary.
- clean_values: Cleans up issue data by replacing None values with a placeholder, converting values to strings, and
truncating overly long values.
- massage_issue_list: Processes a list of JIRA issues, applying flattening, filtering, and sorting, and prepares the
data for display.

Dependencies:
- EnvFetcher: Used to retrieve environment variables.
- JiraClient: Used to interact with JIRA fields.

This module is intended for use in a command-line interface or script that processes and displays JIRA issue data.
"""

import re
import traceback
from argparse import Namespace
from typing import Any

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.rest.client import JiraClient

DEFAULT_VIEW_COLUMNS = "key,issuetype,status,priority,summary,assignee,reporter,sprint"


def fetch_view_columns() -> list[str] | None:
    """
    Fetch view columns from EnvFetcher or use standard Jira columns.
    If any entry contains 'JIRA.......FIELD', fetch the corresponding environment variable.

    Arguments:
    No arguments.

    Return:
    List[str]: A list of view columns where each column may be replaced with an environment variable value.

    Exceptions:
    No exceptions are raised.
    """
    columns = EnvFetcher.get("JIRA_VIEW_COLUMNS", default=DEFAULT_VIEW_COLUMNS)
    if columns:
        column_list = columns.split(",")
        # Iterate through each column, check if it contains 'JIRA' and fetch the corresponding env variable if necessary
        for i, column in enumerate(column_list):
            column = column.strip()
            if "JIRA" in column:
                # Fetch the corresponding environment variable if it contains 'JIRA'
                env_value = EnvFetcher.get(column)
                if env_value:
                    column_list[i] = env_value
        return column_list
    return None


def get_sorted_columns(sort_string: str) -> list[tuple[str, str]]:
    """
    Parse the sort argument and return a list of tuples containing column names and corresponding order.

    Arguments:
    - sort_string (str): A string representing the sort argument with columns and order separated by commas.

    Return:
    - List[Tuple[str, str]]: A list of tuples where each tuple contains a column name and its corresponding order
    (either "asc" for ascending or "desc" for descending).

    Side Effects:
    None
    """
    sort_columns = []
    for sort_item in sort_string.split(","):
        sort_item = sort_item.strip()
        # Check if '=' exists in the sort_item
        if "=" in sort_item:
            col, order = sort_item.split("=")
            sort_columns.append(
                (
                    col.strip(),
                    (order.strip().lower() if order.strip() in ["asc", "desc"] else "asc"),
                )
            )
        else:
            # If no '=' is found, assume ascending order
            sort_columns.append((sort_item.strip(), "asc"))
    return sort_columns


def filter_columns(issue: dict, view_columns: list[str]) -> list[str]:
    """
    Filter the columns based on view_columns.

    Arguments:
    - issue (dict): A dictionary representing an issue with column names as keys.
    - view_columns (List[str]): A list of column names to filter.

    Return:
    - List[str]: A list of values from the issue dictionary corresponding to the columns present in view_columns.
    """
    result = []
    for col in view_columns:
        if col in issue:
            result.append(issue[col])
    return result


def sort_rows(rows: list[tuple], sort_columns: list[tuple[str, str]], headers: list[str]) -> list[tuple]:
    """
    Sort the rows based on the specified columns.

    Arguments:
    - rows (List[Tuple]): A list of tuples representing the rows to be sorted.
    - sort_columns (List[Tuple[str, str]]): A list of tuples where each tuple contains the column name and the sort
    order ("asc" or "desc").
    - headers (List[str]): A list of column headers used to map column names to indices.

    Return:
    - List[Tuple]: A list of tuples representing the sorted rows based on the specified columns.

    Exceptions:
    - Any exception that occurs during the sorting process will be caught and printed with details.
    """
    try:
        for col, order in reversed(sort_columns):
            col_index = headers.index(col)  # Use headers passed as an argument

            def row_key(row: tuple, index: int = col_index):
                return row[index]

            rows.sort(key=row_key, reverse=order == "desc")
    except (ValueError, IndexError) as e:
        print("Error sorting rows based on the columns.")
        print(f"Error details: {e}")
        traceback.print_exc()
    return rows


def format_and_print_rows(rows: list[tuple], headers: list[str], jira_client: JiraClient) -> None:
    """
    Format the rows to match the columns and print.

    Arguments:
    - rows: List of tuples representing the rows to be formatted.
    - headers: List of strings representing the column headers.
    - jira_client: JiraClient object used to interact with Jira for field name retrieval.

    Side Effects:
    - Modifies the headers list to update JIRA field names if necessary.

    Note: The function does not return any value.
    """
    max_summary_length = 60

    # Reverse the operation: Replace column names with environment variable keys
    updated_headers = []
    for header in headers:
        matched = False
        if "customfield_" in header:  # Check if header is a JIRA_* field
            # Fetch the real field name from JiraClient's get_field_name method
            real_field_name = jira_client.get_field_name(header)
            if real_field_name:
                updated_headers.append(real_field_name)  # Use the real field name
                matched = True
        if not matched:
            updated_headers.append(header)  # Keep the original header if no match found

    summary_index = updated_headers.index("summary") if "summary" in updated_headers else -1

    # Ensure that the rows match the expected number of columns
    # for r in rows:
    #     if len(r) != len(updated_headers):
    #         print(
    #             f"Warning: Row length mismatch. Expected {len(updated_headers)} columns but got {len(r)}."
    #         )
    # Pad the row with placeholders to match the length of updated_headers
    # while len(r) < len(updated_headers):
    #     r = r + ("—",)  # Append placeholder values to match length

    # Calculate the column widths dynamically based on the longest content
    # try:
    widths = [
        max(
            len(header),
            max(
                (
                    (len(str(r.get(header, ""))) if isinstance(r, dict) else (len(str(r[i])) if i < len(r) else 0))
                    for r in rows
                ),
                default=0,
            ),
        )
        for i, header in enumerate(updated_headers)
    ]
    # except Exception as e:
    #     raise e

    # Ensure that the summary column has a maximum width
    if summary_index != -1:
        widths[summary_index] = min(widths[summary_index], max_summary_length)

    # Capitalize the first letter of each word in the header for better readability
    updated_headers = [h.title() for h in updated_headers]

    # Format the header with proper alignment
    header_fmt = " | ".join(h.ljust(w) for h, w in zip(updated_headers, widths))
    print(header_fmt)
    print("-" * len(header_fmt))

    # Truncate long summary fields and print each row
    # truncate_length = 97
    for row in rows:
        row_values = list(row)
        # if summary_index != -1 and len(row_values[summary_index]) > max_summary_length:
        #     row_values[summary_index] = row_values[summary_index][:truncate_length] + " .."
        # Print each row, ensuring the formatting matches the column widths
        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row_values)))


def flatten_fields(issue: dict) -> dict:
    """
    Flatten the fields dictionary into the parent issue dictionary.

    Arguments:
    - issue (dict): A dictionary representing an issue with nested fields.

    Return:
    - dict: The parent issue dictionary with flattened fields.
    """
    if "fields" in issue:
        issue.update(issue.pop("fields"))  # Flatten fields into parent issue
    return issue


def clean_values(rows: list[tuple], placeholder: str = "—", max_length: int = 60) -> list[tuple]:
    """
    Replace None values with a placeholder, convert all values to strings,
    and truncate values longer than max_length.

    Arguments:
    - rows (List[Tuple]): A list of tuples containing values to be cleaned.
    - placeholder (str): The string to replace None values with (default is "—").
    - max_length (int): The maximum length allowed for a value before truncation (default is 60).

    Return:
    - List[Tuple]: A list of tuples with cleaned values where None values are replaced,
    all values are converted to strings, and values longer than max_length are truncated.
    """
    cleaned_rows = []
    for row in rows:
        cleaned_row = []
        for val in row:
            if val is None:
                cleaned_row.append(placeholder)
            else:
                if isinstance(val, dict):
                    if "displayName" in val:
                        val = val["displayName"]
                    elif "name" in val:
                        val = val["name"]
                    elif "value" in val:
                        val = val["value"]

                if isinstance(val, float) and val.is_integer():
                    val = int(val)

                val_str = str(val).strip()
                val_str = val_str.replace("\n", " ")
                if len(val_str) > max_length:
                    cleaned_row.append(val_str[:max_length])
                else:
                    cleaned_row.append(val_str)
        cleaned_rows.append(tuple(cleaned_row))
    return cleaned_rows


def _extract_active_sprint(sprints) -> str:
    """Extract the active sprint name from a list of sprint data."""
    if not sprints:
        return "—"
    for s in sprints:
        if isinstance(s, dict):
            if s.get("state", "").lower() == "active" and s.get("name"):
                return s["name"]
        elif isinstance(s, str) and "state=ACTIVE" in s and "name=" in s:
            match = re.search(r"name=([^,]+)", s)
            if match:
                return match.group(1)
    return "—"


def _format_epic_value(issue) -> str | None:
    """Format epic field value for display."""
    epic_value = issue.get(EnvFetcher.get("JIRA_EPIC_FIELD", ""), None) or issue.get("epic", None)
    if not epic_value:
        return "—"
    if isinstance(epic_value, str):
        return epic_value
    if isinstance(epic_value, dict):
        return epic_value.get("key", epic_value.get("name", "—"))
    return str(epic_value)


def _assignee_value(issue) -> str:
    """Return the assignee's display name, or "Unassigned" when unset."""
    return issue["assignee"]["displayName"] if issue.get("assignee") else "Unassigned"


def _reporter_value(issue) -> str | None:
    """Return the reporter's display name, or a placeholder when unset."""
    reporter = issue.get("reporter")
    if reporter and isinstance(reporter, dict):
        return reporter.get("displayName", reporter.get("name", "—"))
    return str(reporter) if reporter else "—"


_ROW_VALUE_GETTERS = {
    "key": lambda issue: issue["key"],
    "status": lambda issue: issue["status"]["name"],
    "assignee": _assignee_value,
    "reporter": _reporter_value,
    "priority": lambda issue: issue.get("priority", {}).get("name", "—"),
    "summary": lambda issue: issue["summary"],
}


def _build_row_value(col, issue, sprint) -> str | None:
    """Build a single row value for the given column."""
    getter = _ROW_VALUE_GETTERS.get(col)
    if getter is not None:
        return getter(issue)
    if col == "sprint":
        return sprint
    if col == "epic" or col == EnvFetcher.get("JIRA_EPIC_FIELD", ""):
        return _format_epic_value(issue)
    return issue.get(col, "—")


def massage_issue_list(args: Namespace, issues: list[dict]):
    """
    Massage the provided issue list by flattening fields, applying view columns, and sorting rows.

    Arguments:
    - args (Namespace): A namespace object containing arguments.
    - issues (list[dict]): A list of dictionaries representing issues to be processed.

    Return:
    - Tuple: A tuple containing the headers (list of strings) and rows (list of tuples) of processed data.

    Exceptions:
    - No exceptions are raised within this function.
    """
    issues = [flatten_fields(issue) for issue in issues]

    view_columns = fetch_view_columns()
    headers = view_columns if view_columns else list(issues[0].keys())

    rows: list[tuple] = []
    for issue in issues:
        sprint_field = EnvFetcher.get("JIRA_SPRINT_FIELD", "")
        sprints = issue.get(sprint_field, []) if sprint_field else []
        sprint = _extract_active_sprint(sprints)
        row_data = [_build_row_value(col, issue, sprint) for col in headers]
        rows.append(tuple(row_data))

    rows = clean_values(rows)

    if hasattr(args, "sort") and args.sort:
        sort_columns = get_sorted_columns(args.sort)
        rows = sort_rows(rows, sort_columns, headers)

    return headers, rows


def search_jira_issues(
    client: Any,
    jql: str,
    max_results: int,
    order_by: str | None = None,
    include_epic: bool = False,
    env_get: Any = None,
) -> list[dict]:
    """
    Search Jira issues with the field set shared by list and search commands.

    Arguments:
    - client: Jira client that accepts request(method, path, params=...).
    - jql: JQL query string.
    - max_results: Maximum number of issues to return.
    - order_by: Optional orderBy parameter. Omitted from the request when empty.
    - include_epic: Include the epic custom field when it is configured.
    - env_get: Callable matching EnvFetcher.get. Defaults to EnvFetcher.get.

    Return:
    - List of issue dictionaries from the search response.
    """
    get_env = env_get or EnvFetcher.get
    fields_to_include = [
        "key",
        "summary",
        "status",
        "assignee",
        "reporter",
        "priority",
        "issuetype",
        "created",
        "updated",
        "components",
    ]

    for env_name in (
        "JIRA_SPRINT_FIELD",
        "JIRA_STORY_POINTS_FIELD",
        "JIRA_BLOCKED_FIELD",
    ):
        custom_field = get_env(env_name, "")
        if custom_field:
            fields_to_include.append(custom_field)

    if include_epic:
        epic_field = get_env("JIRA_EPIC_FIELD", "")
        if epic_field:
            fields_to_include.append(epic_field)

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": ",".join(fields_to_include),
    }
    if order_by:
        params["orderBy"] = order_by

    response = client.request("GET", "/rest/api/2/search", params=params)
    return response.get("issues", [])
