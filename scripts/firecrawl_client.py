"""Firecrawl v2 URLs and response parsing.

v1 scrape and search return HTTP 410 after 2026-12-10 15:00 UTC. Paths are
unchanged aside from the version segment. Scrape markdown still lives at
``data.markdown`` and page metadata at ``data.metadata``.

Search is the shape change: v2 groups hits by source. Web results are
``data.web`` (each item still has ``url``, ``title``, ``description``).
``data.news`` and ``data.images`` appear only when those sources are
requested. v1 returned a flat list at ``data``. The default search limit
also moved from 5 to 10; every caller in this repo passes ``limit``
explicitly, so request bodies stay the same. Search calls do not send
``scrapeOptions`` (v1 search did not scrape result pages either). If a
caller adds ``scrapeOptions``, it must include ``maxAge: 0`` and
``proxy: "basic"``.

v2 scrape defaults that differ from the v1 calls this repo made, and how
they are kept:

- ``maxAge`` is 2 days on v2. These calls never passed it; v1 treated that
  as a fresh scrape. ``scrape_body`` always sends ``maxAge: 0``.
- ``proxy`` defaults to ``auto`` on v2, which retries on an enhanced proxy.
  v1 used ``basic``. ``scrape_body`` always sends ``proxy: "basic"``.
- Server ``timeout`` defaults to 60s on v2. Callers whose HTTP client
  already stops at 60s match that. The transcript-page client waits 120s,
  so that body sets ``timeout: 120000``.
- ``onlyMainContent``, ``blockAds``, and ``removeBase64Images`` default to
  true on both. ``skipTlsVerification`` defaults to false on both.
  ``storeInCache`` defaults to true on both.
- ``parsePDF`` stayed on by default; v2's extra image parser only applies
  to image URLs, which this pipeline does not scrape.

Callers keep their own HTTP client, timeout, retry, and error handling.
"""

from __future__ import annotations

FIRECRAWL_API = "https://api.firecrawl.dev/v2"
SCRAPE_URL = f"{FIRECRAWL_API}/scrape"
SEARCH_URL = f"{FIRECRAWL_API}/search"

# v2's default is 172800000 (2 days). 0 disables the cache read.
SCRAPE_MAX_AGE_MS = 0


def scrape_body(url: str, **extra) -> dict:
    """JSON body for POST /v2/scrape. Fresh (``maxAge`` 0) and ``proxy`` basic.

    v2's default proxy is ``auto``, which retries on an enhanced proxy.
    v1 used ``basic``. ``extra`` is merged after the defaults, so a caller
    can set ``onlyMainContent`` or the server ``timeout`` (milliseconds).
    Passing ``maxAge`` or ``proxy`` overrides these pins; don't.
    """
    body = {
        "url": url,
        "formats": ["markdown"],
        "maxAge": SCRAPE_MAX_AGE_MS,
        "proxy": "basic",
    }
    body.update(extra)
    return body


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
