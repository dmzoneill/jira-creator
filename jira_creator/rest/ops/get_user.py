def get_user(request_fn, username: str) -> dict:
    return request_fn("GET", "/rest/api/2/user", params={"username": username})
