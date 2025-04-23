from core.env_fetcher import EnvFetcher


def set_story_epic(request_fn, issue_key, epic_key):
    """
    Set the epic for a specific JIRA issue.
    
    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the JIRA issue to update.
    - epic_key (str): The key of the epic to set for the issue.
    
    Side Effects:
    - Modifies the JIRA issue specified by 'issue_key' to set the epic to the one specified by 'epic_key'.
    """

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {EnvFetcher.get("JIRA_EPIC_FIELD"): epic_key}},
    )
