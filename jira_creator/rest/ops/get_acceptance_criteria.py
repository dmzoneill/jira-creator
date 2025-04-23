from core.env_fetcher import EnvFetcher


def get_acceptance_criteria(request_fn, issue_key):
    """
    Retrieve the acceptance criteria for a given JIRA issue.
    
    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the JIRA issue for which acceptance criteria are needed.
    
    Return:
    - str: The acceptance criteria for the specified JIRA issue. If not found, an empty string is returned.
    
    Exceptions:
    - Raises an exception if there is an issue with the HTTP request or if the acceptance criteria field is not found.
    
    Side Effects:
    - None
    """

    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"].get(
        EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"), ""
    )
