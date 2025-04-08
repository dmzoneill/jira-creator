import hashlib
import json
import os

from core.env_fetcher import EnvFetcher


def get_cache_path():
    return os.path.expanduser("~/.config/rh-issue/ai-hashes.json")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cache():
    if os.path.exists(get_cache_path()):
        with open(get_cache_path(), "r") as f:
            return json.load(f)
    return {}


def save_cache(data):
    cache_dir = os.path.dirname(get_cache_path())

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)  # Ensure directory exists

    with open(get_cache_path(), "w") as f:
        json.dump(data, f, indent=2)


def load_and_cache_issue(issue_key):
    """Load cache and get the cached values for a given issue key."""
    cache = load_cache()
    cached = cache.get(issue_key, {})
    return cache, cached


def validate_progress(status, assignee, problems, issue_status):
    """Validate if the issue is assigned when it's in progress."""
    if status == "In Progress" and not assignee:
        problems.append("❌ Issue is In Progress but unassigned")
        issue_status["Progress"] = False
    else:
        issue_status["Progress"] = True


def validate_epic_link(issue_type, status, epic_link, problems, issue_status):
    """Validate if an issue has an assigned epic link."""
    epic_exempt_types = ["Epic"]
    epic_exempt_statuses = ["New", "Refinement"]
    if (
        issue_type not in epic_exempt_types
        and not (
            issue_type in ["Bug", "Story", "Spike", "Task"]
            and status in epic_exempt_statuses
        )
        and not epic_link
    ):
        problems.append("❌ Issue has no assigned Epic")
        issue_status["Epic"] = False
    else:
        issue_status["Epic"] = True


def validate_sprint(status, sprint_field, problems, issue_status):
    """Validate if the issue is assigned to a sprint when in progress."""
    if status == "In Progress" and not sprint_field:
        problems.append("❌ Issue is In Progress but not assigned to a Sprint")
        issue_status["Sprint"] = False
    else:
        issue_status["Sprint"] = True


def validate_priority(priority, problems, issue_status):
    """Validate if priority is set."""
    if not priority:
        problems.append("❌ Priority not set")
        issue_status["Priority"] = False
    else:
        issue_status["Priority"] = True


def validate_story_points(story_points, status, problems, issue_status):
    """Validate if story points are assigned, unless the status is 'Refinement' or 'New'."""
    if story_points is None and status not in ["Refinement", "New"]:
        problems.append("❌ Story points not assigned")
        issue_status["Story P."] = False
    else:
        issue_status["Story P."] = True


def validate_blocked(blocked_value, blocked_reason, problems, issue_status):
    """Validate if blocked issues have a reason."""
    if blocked_value == "True" and not blocked_reason:
        problems.append("❌ Issue is blocked but has no blocked reason")
        issue_status["Blocked"] = False
    else:
        issue_status["Blocked"] = True


def validate_field_with_ai(
    field_name,
    field_value,
    field_hash,
    cached_field_hash,
    ai_provider,
    problems,
    issue_status,
):
    if field_value:
        # Ensure the field hash comparison is correct
        if field_hash != cached_field_hash:
            reviewed = ai_provider.improve_text(
                f"""Check the quality of the following Jira {field_name}.
                Is it clear, concise, and informative? Respond with 'OK' if fine or explain why not.""",
                field_value,
            )
            if "ok" not in reviewed.lower():  # If AI response is not OK
                problems.append(f"❌ {field_name}: {reviewed.strip()}")
                issue_status[field_name] = False
            else:
                cached_field_hash = field_hash  # Update the cached hash here
                issue_status[field_name] = True
        elif field_hash == cached_field_hash and "ok" not in field_value.lower():
            problems.append(f"❌ {field_name}: {field_value.strip()}")
            issue_status[field_name] = False

    return cached_field_hash  # Return the updated hash to use in the next validation


def cli_validate_issue(fields, ai_provider):
    problems = []
    issue_status = {}

    # Extract and validate basic fields
    issue_key = fields.get("key")
    if not issue_key:
        return problems, issue_status

    status = fields.get("status", {}).get("name")
    assignee = fields.get("assignee")
    epic_link = fields.get(EnvFetcher.get("JIRA_EPIC_FIELD"))
    sprint_field = fields.get(EnvFetcher.get("JIRA_SPRINT_FIELD"))
    priority = fields.get("priority")
    story_points = fields.get(EnvFetcher.get("JIRA_STORY_POINTS_FIELD"))
    blocked_value = fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value")
    blocked_reason = fields.get(EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"))

    # Load cache for the issue
    cache, cached = load_and_cache_issue(issue_key)

    # Validate various fields
    validate_progress(status, assignee, problems, issue_status)
    validate_epic_link(
        fields.get("issuetype", {}).get("name"),
        status,
        epic_link,
        problems,
        issue_status,
    )
    validate_sprint(status, sprint_field, problems, issue_status)
    validate_priority(priority, problems, issue_status)
    validate_story_points(story_points, status, problems, issue_status)
    validate_blocked(blocked_value, blocked_reason, problems, issue_status)

    # Validate summary, description, and acceptance criteria using AI
    summary = fields.get("summary", "")
    summary_hash = sha256(summary) if summary else None
    cached["summary_hash"] = validate_field_with_ai(
        "Summary",
        summary,
        summary_hash,
        cached.get("summary_hash"),
        ai_provider,
        problems,
        issue_status,
    )

    description = fields.get("description", "")
    description_hash = sha256(description) if description else None
    cached["description_hash"] = validate_field_with_ai(
        "Description",
        description,
        description_hash,
        cached.get("description_hash"),
        ai_provider,
        problems,
        issue_status,
    )

    acceptance_criteria = fields.get(
        EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"), ""
    )
    acceptance_criteria_hash = (
        sha256(acceptance_criteria) if acceptance_criteria else None
    )
    cached["acceptance_criteria_hash"] = validate_field_with_ai(
        "Acceptance Criteria",
        acceptance_criteria,
        acceptance_criteria_hash,
        cached.get("acceptance_criteria_hash"),
        ai_provider,
        problems,
        issue_status,
    )

    # Save the updated cache
    cache[issue_key] = cached
    save_cache(cache)

    return problems, issue_status
