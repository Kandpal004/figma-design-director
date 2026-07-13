"""
firecrawl.py — Firecrawl adapter (robust crawl/scrape → clean data for LLMs).

Turns a URL into clean markdown + html + links, handling JS-heavy pages better than a raw
Playwright pass. Used for the "Crawl Every Page" pipeline step. Activates when
FIRECRAWL_API_KEY is set; otherwise callers fall back to extract/extractor.py (Playwright).

No third-party dependency — uses urllib so it works on any Python.
Docs: https://docs.firecrawl.dev  (POST /v1/scrape and /v1/crawl)
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"
CRAWL_URL = "https://api.firecrawl.dev/v1/crawl"


def available() -> bool:
    return bool(os.environ.get("FIRECRAWL_API_KEY"))


def _post(endpoint: str, payload: dict, timeout: int = 120) -> dict:
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        raise RuntimeError("FIRECRAWL_API_KEY not set")
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def scrape(url: str, formats: tuple[str, ...] = ("markdown", "links")) -> dict:
    """Single page → {markdown, links, metadata}. Grounded, clean, LLM-ready."""
    resp = _post(SCRAPE_URL, {"url": url, "formats": list(formats)})
    return resp.get("data", resp)


def scrape_to(url: str, out_dir: Path) -> dict:
    """Scrape and write crawl.md into output/<site>/ for the design subagents to read."""
    data = scrape(url)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = data.get("markdown", "")
    (out_dir / "crawl.md").write_text(md, encoding="utf-8")
    return {"chars": len(md), "links": len(data.get("links", []) or []),
            "title": (data.get("metadata") or {}).get("title", "")}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python extract/firecrawl.py <url>")
        raise SystemExit(2)
    if not available():
        print("FIRECRAWL_API_KEY not set — set it in .env to enable Firecrawl.")
        raise SystemExit(1)
    d = scrape(sys.argv[1])
    print((d.get("markdown", ""))[:1500])
