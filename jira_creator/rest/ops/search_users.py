def search_users(request_fn, query: str, max_results: int = 10) -> list:
    return request_fn(
        "GET",
        "/rest/api/2/user/search",
        params={"username": query, "maxResults": max_results},
    )
