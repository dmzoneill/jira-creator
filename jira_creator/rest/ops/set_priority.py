def set_priority(request_fn, issue_key, priority):
    # Put this somewhere else
    priorities = {
        "critical": "Critical",
        "major": "Major",
        "normal": "Normal",
        "minor": "Minor",
    }

    priority = (
        priorities[priority.lower()] if priority.lower() in priorities else "Normal"
    )

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {"priority": {"name": priority}}},
    )
