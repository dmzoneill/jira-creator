def list_sprints(request_fn, board_id: str) -> list[str]:
    path = f"/rest/agile/1.0/board/{board_id}/sprint"
    res = request_fn("GET", path)
    sprints = res.get("values")
    open_sprints = [sprint["name"] for sprint in sprints if sprint["state"] != "closed"]
    return open_sprints
