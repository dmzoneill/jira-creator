def get_current_user(request_fn):
    user = request_fn("GET", "/rest/api/2/myself")
    return user.get("name") or user.get("accountId")
