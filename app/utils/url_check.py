from __future__ import annotations
import asyncio, ipaddress
from urllib.parse import urlparse
import httpx

ALLOWED_SCHEMES = {"http", "https"}
REQUEST_TIMEOUT = 5.0          # seconds
MAX_CONCURRENCY = 8            # safety so we don't hammer sites

def _looks_safe_http_url(url: str) -> bool:
    try:
        u = urlparse(url)
    except Exception:
        return False
    if u.scheme.lower() not in ALLOWED_SCHEMES:
        return False
    if not u.netloc:
        return False
    # Basic private IP / bare IP guard
    host = u.hostname or ""
    try:
        ip = ipaddress.ip_address(host)
        # reject private/loopback/link-local
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        # not an IP, fine (a normal domain)
        pass
    return True

async def is_valid_url(url: str) -> bool:
    if not _looks_safe_http_url(url):
        return False
    try:
        headers = {"User-Agent": "AgenticTutor/1.0 (+https://example.com)"}
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as c:
            # Try HEAD first
            r = await c.head(url)
            if r.status_code >= 400:
                # Some hosts don't implement HEAD well
                r = await c.get(url)
            return 200 <= r.status_code < 400
    except Exception:
        return False

async def scrub_task_links(tasks: list[dict]) -> list[dict]:
    """
    For a list of task dicts (with optional 'resource_ref'), drop any invalid links.
    Returns the same list (mutated) for convenience.
    """
    # Build (index, url) pairs to check
    to_check = [(i, t.get("resource_ref")) for i, t in enumerate(tasks) if t.get("resource_ref")]
    if not to_check:
        return tasks

    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def _checked(idx: int, url: str) -> tuple[int, bool]:
        async with sem:
            return idx, await is_valid_url(url)

    results = await asyncio.gather(*(_checked(i, u) for i, u in to_check), return_exceptions=True)

    for (i, _), ok in zip(to_check, results):
        valid = (isinstance(ok, tuple) and ok[1] is True)
        if not valid:
            tasks[i]["resource_ref"] = None

    return tasks