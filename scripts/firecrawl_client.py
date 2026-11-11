"""Firecrawl v2 URLs and response parsing.

v1 scrape and search return HTTP 410 after 2026-12-10 15:00 UTC. Paths are
unchanged aside from the version segment. Scrape markdown still lives at
``data.markdown`` and page metadata at ``data.metadata``.

Search is the shape change: v2 groups hits by source. Web results are
``data.web`` (each item still has ``url``, ``title``, ``description``).
``data.news`` and ``data.images`` appear only when those sources are
requested. v1 returned a flat list at ``data``. The default search limit
also moved from 5 to 10; every caller in this repo passes ``limit``
explicitly, so request bodies stay the same.

Callers keep their own HTTP client, timeout, retry, and error handling.
"""

from __future__ import annotations

FIRECRAWL_API = "https://api.firecrawl.dev/v2"
SCRAPE_URL = f"{FIRECRAWL_API}/scrape"
SEARCH_URL = f"{FIRECRAWL_API}/search"


def search_web_results(payload) -> list:
    """Return the web hit list from a v2 search JSON body.

    Missing ``data`` or ``data.web`` is an empty result set. A non-object
    body, a flat v1-style ``data`` list, or a non-list ``web`` value raises
    so existing retry / warn handlers still see a bad response.
    """
    if payload is None:
        return []
    if not isinstance(payload, dict):
        raise TypeError("Firecrawl search response was not a JSON object")
    if "data" not in payload or payload.get("data") is None:
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        raise TypeError(
            "Firecrawl v2 search response data is not an object (expected data.web)"
        )
    if "web" not in data or data.get("web") is None:
        return []
    web = data.get("web")
    if not isinstance(web, list):
        raise TypeError("Firecrawl v2 search data.web is not a list")
    return web
