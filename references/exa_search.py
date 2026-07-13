"""
exa_search.py — Exa AI Search adapter (neural/semantic web search).

Powers the "Research Competitors → Find Better Solutions" pipeline steps: given a category or
a design question, find the best real references and best-practice sources (not keyword spam —
Exa is embeddings-based). Activates when EXA_API_KEY is set.

No third-party dependency — uses urllib.
Docs: https://docs.exa.ai  (POST https://api.exa.ai/search)
"""

from __future__ import annotations

import json
import os
import urllib.request

SEARCH_URL = "https://api.exa.ai/search"


def available() -> bool:
    return bool(os.environ.get("EXA_API_KEY"))


def search(query: str, num: int = 8, category: str | None = None,
           include_text: bool = True) -> list[dict]:
    """Return [{title, url, snippet}] semantically matched to the query."""
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise RuntimeError("EXA_API_KEY not set")
    payload: dict = {"query": query, "numResults": num, "type": "auto"}
    if category:
        payload["category"] = category
    if include_text:
        payload["contents"] = {"text": {"maxCharacters": 500}}
    req = urllib.request.Request(
        SEARCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"x-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for res in data.get("results", []):
        out.append({
            "title": res.get("title", ""),
            "url": res.get("url", ""),
            "snippet": (res.get("text", "") or "")[:400],
        })
    return out


def research_competitors(brand_or_category: str, num: int = 8) -> list[dict]:
    """Find best-in-class ecommerce references + UX best-practices for a category/brand."""
    q = (f"Best-in-class premium ecommerce product page design and UX for "
         f"{brand_or_category}. High-converting PDP examples and CRO best practices.")
    return search(q, num=num)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print('usage: python references/exa_search.py "<query>"')
        raise SystemExit(2)
    if not available():
        print("EXA_API_KEY not set — set it in .env to enable Exa search.")
        raise SystemExit(1)
    for r in search(sys.argv[1]):
        print(f"- {r['title']}\n  {r['url']}")
