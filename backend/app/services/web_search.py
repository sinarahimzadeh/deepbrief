import ipaddress
from collections.abc import Sequence
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from app.schemas.research import ResearchSource

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TRACKING_QUERY_PARAMETERS = {
    "fbclid",
    "gclid",
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


class SearchProviderError(RuntimeError):
    """Raised when the configured web-search provider cannot return evidence."""


class SearchLimitReachedError(SearchProviderError):
    """Raised when Tavily's free keyless search limit has been reached."""


class SearchProvider(Protocol):
    async def search(self, query: str, *, max_results: int) -> list[dict[str, Any]]: ...


def canonicalize_url(value: str) -> str | None:
    """Return a safe, stable public HTTP URL for deduplication and display."""

    try:
        parsed = urlsplit(value.strip())
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        return None

    normalized_host = hostname.rstrip(".").lower()
    if normalized_host == "localhost" or normalized_host.endswith(".local"):
        return None

    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        pass
    else:
        if not address.is_global:
            return None

    default_port = 80 if parsed.scheme.lower() == "http" else 443
    netloc = normalized_host if port in {None, default_port} else f"{normalized_host}:{port}"
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.casefold() not in TRACKING_QUERY_PARAMETERS
    ]
    return urlunsplit(
        (
            parsed.scheme.lower(),
            netloc,
            path,
            urlencode(sorted(query_items)),
            "",
        )
    )


class TavilySearchProvider:
    """Small async Tavily client using its free, rate-limited keyless mode."""

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, *, max_results: int) -> list[dict[str, Any]]:
        headers = {
            "Content-Type": "application/json",
            "X-Tavily-Access-Mode": "keyless",
        }
        payload = {
            "query": query,
            "search_depth": "basic",
            "max_results": max(1, min(max_results, 5)),
            "topic": "general",
            "include_answer": False,
            "include_raw_content": False,
            "include_published_date": True,
            "safe_search": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(TAVILY_SEARCH_URL, headers=headers, json=payload)
        except httpx.HTTPError as error:
            raise SearchProviderError("Web search is temporarily unavailable") from error

        if response.status_code in {429, 432, 433}:
            raise SearchLimitReachedError("The free web-search limit has been reached")
        if response.status_code >= 400:
            raise SearchProviderError("Web search is temporarily unavailable")

        try:
            body = response.json()
        except ValueError as error:
            raise SearchProviderError("Web search returned an invalid response") from error

        results = body.get("results")
        if not isinstance(results, list):
            raise SearchProviderError("Web search returned no result list")
        return [item for item in results if isinstance(item, dict)]


async def collect_sources(
    queries: Sequence[str],
    *,
    researcher_index: int,
    max_sources: int,
    provider: SearchProvider | None = None,
) -> list[ResearchSource]:
    """Run bounded searches and return the best unique public sources."""

    search_provider = provider or TavilySearchProvider()
    candidates: dict[str, ResearchSource] = {}

    for query in queries[:4]:
        raw_results = await search_provider.search(query, max_results=min(max_sources, 5))
        for raw in raw_results:
            canonical_url = canonicalize_url(str(raw.get("url", "")))
            if canonical_url is None:
                continue

            snippet = " ".join(str(raw.get("content", "")).split())[:4000]
            if not snippet:
                continue

            domain = urlsplit(canonical_url).hostname or "unknown"
            score_value = raw.get("score")
            score = float(score_value) if isinstance(score_value, (int, float)) else None
            if score is not None:
                score = max(0.0, min(score, 1.0))

            source = ResearchSource(
                source_key=f"R{researcher_index}S1",
                title=" ".join(str(raw.get("title") or domain).split())[:300],
                url=canonical_url,
                domain=domain,
                snippet=snippet,
                query=query,
                score=score,
                published_date=(
                    str(raw["published_date"]) if raw.get("published_date") else None
                ),
            )
            existing = candidates.get(canonical_url)
            if existing is None or (source.score or 0) > (existing.score or 0):
                candidates[canonical_url] = source

    ranked = sorted(candidates.values(), key=lambda source: source.score or 0, reverse=True)
    selected = ranked[:max_sources]
    return [
        source.model_copy(update={"source_key": f"R{researcher_index}S{position}"})
        for position, source in enumerate(selected, start=1)
    ]
