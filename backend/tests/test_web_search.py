import asyncio
from typing import Any

from app.services.web_search import canonicalize_url, collect_sources


class FakeSearchProvider:
    async def search(self, query: str, *, max_results: int) -> list[dict[str, Any]]:
        return [
            {
                "title": "Repeated source",
                "url": "https://Example.com/article/?utm_source=test",
                "content": f"Evidence returned for {query}.",
                "score": 0.8,
            },
            {
                "title": f"Unique source for {query}",
                "url": f"https://example.org/{query.replace(' ', '-')}",
                "content": f"Additional evidence returned for {query}.",
                "score": 0.7,
            },
        ][:max_results]


def test_canonicalize_url_removes_tracking_and_rejects_private_hosts() -> None:
    assert (
        canonicalize_url("HTTPS://Example.com/story/?utm_source=newsletter&b=2&a=1#section")
        == "https://example.com/story?a=1&b=2"
    )
    assert canonicalize_url("http://127.0.0.1/internal") is None
    assert canonicalize_url("file:///etc/passwd") is None


def test_collect_sources_deduplicates_and_assigns_stable_keys() -> None:
    sources = asyncio.run(
        collect_sources(
            ["first query", "second query"],
            researcher_index=2,
            max_sources=3,
            provider=FakeSearchProvider(),
        )
    )

    assert len(sources) == 3
    assert [source.source_key for source in sources] == ["R2S1", "R2S2", "R2S3"]
    assert len({source.url for source in sources}) == 3
    assert all("utm_" not in source.url for source in sources)
