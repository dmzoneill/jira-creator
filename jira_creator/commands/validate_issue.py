import hashlib
import json
import os

CACHE_PATH = os.path.expanduser("~/.config/rh-issue/ai-hashes.json")


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_cache(data):
    cache_dir = os.path.dirname(CACHE_PATH)
    # Debugging: print the cache directory being used

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)  # Ensure directory exists

    with open(CACHE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def handle(fields, ai_provider):
    problems = []
    issue_status = {}

    # Get the issue key and ensure it exists before proceeding
    issue_key = fields.get("key")
    if not issue_key:
        return problems, issue_status  # Return early if no issue key is present

    issue_type = fields.get("issuetype", {}).get("name")
    status = fields.get("status", {}).get("name")
    summary = fields.get("summary", "")
    description = fields.get("description", "")
    acceptance_criteria = fields.get("customfield_12315940")  # Acceptance Criteria
    epic_link = fields.get("customfield_12311140")
    sprint_field = fields.get("customfield_12310940")
    priority = fields.get("priority")
    story_points = fields.get("customfield_12310243")
    blocked_value = fields.get("customfield_12316543", {}).get("value")
    blocked_reason = fields.get("customfield_12316544")

    summary_hash = sha256(summary) if summary else None
    description_hash = sha256(description) if description else None
    acceptance_criteria_hash = (
        sha256(acceptance_criteria) if acceptance_criteria else None
    )

    cache = load_cache()
    cached = cache.get(issue_key, {})

    # ✅ Basic validations
    if status == "In Progress" and not fields.get("assignee"):
        problems.append("❌ Issue is In Progress but unassigned")
        issue_status["Progress"] = False
    else:
        issue_status["Progress"] = True

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

    if status == "In Progress" and not sprint_field:
        problems.append("❌ Issue is In Progress but not assigned to a Sprint")
        issue_status["Sprint"] = False
    else:
        issue_status["Sprint"] = True

    if not priority:
        problems.append("❌ Priority not set")
        issue_status["Priority"] = False
    else:
        issue_status["Priority"] = True

    if story_points is None and status not in ["Refinement", "New"]:
        problems.append("❌ Story points not assigned")
        issue_status["Story P."] = False
    else:
        issue_status["Story P."] = True

    if blocked_value == "True" and not blocked_reason:
        problems.append("❌ Issue is blocked but has no blocked reason")
        issue_status["Blocked"] = False
    else:
        issue_status["Blocked"] = True

    # Validate summary
    if summary:
        if summary_hash != cached.get("summary_hash"):
            reviewed = ai_provider.improve_text(
                "Check the quality of the following Jira summary. Is it clear, concise, and informative? Respond with 'OK' if fine or explain why not.",
                summary,
            )
            if "ok" not in reviewed.lower():
                problems.append(f"❌ Summary: {reviewed.strip()}")
                issue_status["Summary"] = False
            else:
                cached["summary_hash"] = summary_hash
                issue_status["Summary"] = True

    # Validate description
    if description:
        if description_hash != cached.get("description_hash"):
            reviewed = ai_provider.improve_text(
                "Check the quality of the following Jira description. Is it well-structured, informative, and helpful? Respond with 'OK' if fine or explain why not.",
                description,
            )
            if "ok" not in reviewed.lower():
                problems.append(f"❌ Description: {reviewed.strip()}")
                issue_status["Description"] = False
            else:
                cached["description_hash"] = description_hash
                cached["last_ai_description"] = reviewed.strip()  # Store AI suggestion
                issue_status["Description"] = True

        elif (
            "last_ai_description" in cached
            and cached["last_ai_description"].lower() != "ok"
        ):
            # If the description hasn't changed, use the last AI suggestion only if it's not "OK"
            problems.append(f"❌ Description: {cached['last_ai_description']}")
            issue_status["Description"] = False

    # Validate acceptance criteria
    if acceptance_criteria:
        if acceptance_criteria_hash != cached.get("acceptance_criteria_hash"):
            reviewed = ai_provider.improve_text(
                "Check the quality of the following Jira acceptance criteria. Is it clear, concise, and actionable? Respond with 'OK' if fine or explain why not.",
                acceptance_criteria,
            )
            if "ok" not in reviewed.lower():
                problems.append(f"❌ Acceptance Criteria: {reviewed.strip()}")
                issue_status["Acceptance C."] = False
            else:
                cached["acceptance_criteria_hash"] = acceptance_criteria_hash
                cached["last_ai_acceptance_criteria"] = (
                    reviewed.strip()
                )  # Store AI suggestion
                issue_status["Acceptance C."] = True

        elif (
            "last_ai_acceptance_criteria" in cached
            and cached["last_ai_acceptance_criteria"].lower() != "ok"
        ):
            # If the acceptance criteria hasn't changed, use the last AI suggestion only if it's not "OK"
            problems.append(
                f"❌ Acceptance Criteria: {cached['last_ai_acceptance_criteria']}"
            )
            issue_status["Acceptance C."] = False

    # Save cache after processing
    cache[issue_key] = cached
    save_cache(cache)

    return problems, issue_status
