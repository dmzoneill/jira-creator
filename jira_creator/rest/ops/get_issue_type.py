def get_issue_type(request_fn, issue_key):
    """
    Retrieve the type of an issue identified by the given key.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): A string representing the unique key of the issue to retrieve.

    Return:
    - str: A string indicating the type of the issue identified by the provided key.

    Exceptions:
    - This function does not explicitly handle any exceptions. Any exceptions raised during the HTTP request will
    propagate.
    """

    issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
    return issue["fields"]["issuetype"]["name"]
