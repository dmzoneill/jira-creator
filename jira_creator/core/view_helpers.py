import re
import traceback
from argparse import Namespace
from typing import List, Tuple

from core.env_fetcher import EnvFetcher
from rest.client import JiraClient


def fetch_view_columns() -> List[str]:
    """
    Fetch the view columns from EnvFetcher or return None.
    If any entry contains 'JIRA.......FIELD', fetch the environment variable.
    """
    columns = EnvFetcher.get("JIRA_VIEW_COLUMNS")
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


def get_sorted_columns(sort_string: str) -> List[Tuple[str, str]]:
    """Parse the sort argument and return a list of tuples containing column and order."""
    sort_columns = []
    for sort_item in sort_string.split(","):
        sort_item = sort_item.strip()
        # Check if '=' exists in the sort_item
        if "=" in sort_item:
            col, order = sort_item.split("=")
            sort_columns.append(
                (
                    col.strip(),
                    (
                        order.strip().lower()
                        if order.strip() in ["asc", "desc"]
                        else "asc"
                    ),
                )
            )
        else:
            # If no '=' is found, assume ascending order
            sort_columns.append((sort_item.strip(), "asc"))
    return sort_columns


def filter_columns(issue: dict, view_columns: List[str]) -> List[str]:
    """Filter the columns based on view_columns."""
    result = []
    for col in view_columns:
        if col in issue:
            result.append(issue[col])
    return result


def sort_rows(
    rows: List[Tuple], sort_columns: List[Tuple[str, str]], headers: List[str]
) -> List[Tuple]:
    """Sort the rows based on the sort columns."""
    try:
        for col, order in reversed(sort_columns):
            col_index = headers.index(col)  # Use headers passed as an argument
            rows.sort(key=lambda x: x[col_index], reverse=(order == "desc"))
    except Exception as e:
        print("Error sorting rows based on the columns.")
        print(f"Error details: {e}")
        traceback.print_exc()
    return rows


def format_and_print_rows(
    rows: List[Tuple], headers: List[str], jira_client: JiraClient
) -> None:
    """Format the rows to match the columns and print."""
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

    summary_index = (
        updated_headers.index("summary") if "summary" in updated_headers else -1
    )

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
                    (
                        len(str(r.get(header, "")))
                        if isinstance(r, dict)
                        else (
                            len(str(r[i]))  # fmt: skip
                            if i < len(r)
                            else 0
                        )
                    )
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
    for r in rows:
        r = list(r)
        # if summary_index != -1 and len(r[summary_index]) > max_summary_length:
        #     r[summary_index] = r[summary_index][:truncate_length] + " .."
        # Print each row, ensuring the formatting matches the column widths
        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(r)))


def flatten_fields(issue: dict) -> dict:
    """Flatten the fields dictionary into the parent issue dictionary."""
    if "fields" in issue:
        issue.update(issue.pop("fields"))  # Flatten fields into parent issue
    return issue


def clean_values(
    rows: List[Tuple], placeholder: str = "—", max_length: int = 60
) -> List[Tuple]:
    """
    Replace None values with a placeholder, convert all values to strings,
    and truncate values longer than max_length.
    """
    cleaned_rows = []
    for row in rows:
        cleaned_row = []
        for val in row:
            if val is None:
                cleaned_row.append(placeholder)
            else:
                if isinstance(val, dict):
                    if "name" in val:
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


def massage_issue_list(args: Namespace, issues: list[dict]):
    issues = [flatten_fields(issue) for issue in issues]

    # Get the view columns from EnvFetcher or use None
    view_columns = fetch_view_columns()

    headers = view_columns if view_columns else list(issues[0].keys())

    rows: List[Tuple] = []
    for issue in issues:
        sprints = issue.get(EnvFetcher.get("JIRA_SPRINT_FIELD"), [])
        sprint = "-"
        if sprints is not None:
            sprint = next(
                (
                    re.search(r"name=([^,]+)", s).group(1)
                    for s in sprints
                    if "state=ACTIVE" in s and "name=" in s
                ),
                "—",
            )

        # Dynamically create row data based on headers (view_columns or first dict's keys)
        row_data = []
        for col in headers:
            if col == "key":
                row_data.append(issue["key"])
            elif col == "status":
                row_data.append(issue["status"]["name"])
            elif col == "assignee":
                row_data.append(
                    issue["assignee"]["displayName"]
                    if issue.get("assignee")
                    else "Unassigned"
                )
            elif col == "priority":
                row_data.append(issue.get("priority", {}).get("name", "—"))
            elif col == "summary":
                row_data.append(issue["summary"])
            elif col == "sprint":
                row_data.append(sprint)
            else:
                # For any other dynamic fields, append the value directly
                row_data.append(issue.get(col, "—"))

        # If view_columns is set, filter columns based on it
        if view_columns:
            row_data = filter_columns(issue, view_columns)

        rows.append(tuple(row_data))

    # Clean rows by replacing None values with a placeholder
    rows = clean_values(rows)

    # Sort rows if sort is available
    if hasattr(args, "sort") and args.sort:
        sort_columns = get_sorted_columns(args.sort)
        rows = sort_rows(rows, sort_columns, headers)  # Pass headers here

    return headers, rows
