def set_story_epic(request_fn, issue_key, epic_key):
    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {"customfield_12311140": epic_key}},
    )
