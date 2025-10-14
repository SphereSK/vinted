from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

def build_catalog_url(base_url: str, search_text: str = None, category=None, platform_id=None, extra=None, order=None) -> str:
    """
    Construct a valid Vinted catalog URL with query parameters.
    Supports multiple categories and platform IDs.
    search_text is optional - can filter by category/platform only.
    Example output:
        https://www.vinted.sk/catalog?search_text=ps5&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first
    """
    params = {}
    if search_text:
        params["search_text"] = search_text

    if category:
        # Append multiple catalog[] params
        for i, c in enumerate(category):
            params[f"catalog[{i}]"] = c

    if platform_id:
        # Append multiple platform IDs
        for i, p in enumerate(platform_id):
            params[f"video_game_platform_ids[{i}]"] = p

    if order:
        params["order"] = order

    if extra:
        for e in extra:
            if "=" in e:
                k, v = e.split("=", 1)
                params[k] = v

    query_string = urlencode(params, doseq=True)
    return f"{base_url}?{query_string}"


def with_page(url: str, page: int) -> str:
    """
    Append or replace the 'page' query parameter in a given URL.
    """
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    q["page"] = [str(page)]
    new_query = urlencode(q, doseq=True)
    new_url = urlunparse(parsed._replace(query=new_query))
    return new_url
