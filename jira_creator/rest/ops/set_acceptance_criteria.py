from core.env_fetcher import EnvFetcher


def set_acceptance_criteria(request_fn, issue_key, acceptance_criteria):
    payload = {
        "fields": {
            EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"): (
                "" if not acceptance_criteria else str(acceptance_criteria)
            )
        }
    }

    # Perform the PUT request to update the acceptance criteria
    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json=payload,
    )

    print(f"✅ Updated acceptance criteria of {issue_key}")
