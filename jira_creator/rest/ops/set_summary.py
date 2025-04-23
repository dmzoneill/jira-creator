def set_summary(request_fn, issue_key) -> dict:
    """
    Sets a summary for a specific issue in Jira.
    
    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue for which the summary will be set.
    
    Return:
    - dict: A dictionary containing the response from the HTTP POST request.
    
    """

    path = "/rest/api/2/issue/AAP-test_set_summary"
    return request_fn("POST", path, json={})
