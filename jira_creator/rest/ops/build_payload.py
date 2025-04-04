def build_payload(
    summary,
    description,
    issue_type,
    project_key,
    affects_version,
    component_name,
    priority,
    epic_field,
):
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": description,
        "issuetype": {"name": issue_type.capitalize()},
        "priority": {"name": priority},
        "versions": [{"name": affects_version}],
        "components": [{"name": component_name}],
    }

    if issue_type.lower() == "epic":
        fields[epic_field] = summary

    return {"fields": fields}
