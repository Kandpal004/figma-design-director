"""
config.py — wires the Design Director agent together.

- Loads SYSTEM_PROMPT.md as the Director persona (via append-system-prompt file to dodge
  the Windows command-line length limit).
- Registers the 6 subagents from agents/*.md.
- Exposes 3 in-process MCP tools the agent calls: extract_site, run_slop_gate, get_references.

Kept deliberately lean: no Postgres/Redis/Qdrant. The value is in grounding + gates +
human approval, not infrastructure.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    tool,
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
CACHE = ROOT / ".cache"
CACHE.mkdir(exist_ok=True)

# make sibling packages importable when run as a script
import sys
sys.path.insert(0, str(ROOT))

from extract.extractor import extract as _extract, _slug            # noqa: E402
from gates.slop_detector import scan_dir, scan_file                 # noqa: E402
from references.reference_engine import references_for              # noqa: E402
from extract import firecrawl as _firecrawl                         # noqa: E402
from references import exa_search as _exa                           # noqa: E402


# ---------------------------------------------------------------- MCP tools ----

@tool(
    "extract_site",
    "Crawl a URL with a real browser and extract REAL design tokens (fonts, colors, "
    "components, layout, nav, CRO signals), take full-page screenshots, and download real "
    "images. Writes output/<site>/ (tokens.json, grounding.md, images/). Call this BEFORE "
    "designing anything.",
    {"url": str},
)
async def extract_site(args: dict) -> dict:
    url = args["url"]
    tokens = await _extract(url, OUTPUT)
    site = _slug(url)
    fams = [f["family"] for f in tokens["typography"]["families"][:3]]
    cols = [c["color"] for c in tokens["colors"][:6]]
    imgs = len(tokens.get("downloaded_images", []))
    return {"content": [{"type": "text", "text":
        f"Extracted -> output/{site}/\n"
        f"real fonts: {fams}\nreal palette: {cols}\nimages downloaded: {imgs}\n"
        f"grounding brief: output/{site}/grounding.md\n"
        f"tokens: output/{site}/tokens.json"}]}


@tool(
    "run_slop_gate",
    "Scan generated HTML/CSS (a file or a directory) for AI-slop signals: banned fonts, "
    "placeholder images on product/hero slots, cream backgrounds, gradient/shadow/glass "
    "spam, oversized radius. Returns violations. A BLOCK means fix before presenting.",
    {"path": str},
)
async def run_slop_gate(args: dict) -> dict:
    p = Path(args["path"])
    rep = scan_dir(p) if p.is_dir() else scan_file(p)
    return {"content": [{"type": "text", "text": rep.as_text()}],
            "isError": rep.blocked}


@tool(
    "get_references",
    "Given output/<site>/tokens.json, detect the product category and return "
    "category-appropriate PREMIUM benchmark brands to calibrate craft against (never copy).",
    {"tokens_path": str},
)
async def get_references(args: dict) -> dict:
    tokens = json.loads(Path(args["tokens_path"]).read_text(encoding="utf-8"))
    ref = references_for(tokens)
    return {"content": [{"type": "text", "text":
        f"category: {ref.category}\nbenchmarks: {', '.join(ref.brands)}\n"
        f"craft notes: {ref.craft_notes}"}]}


@tool(
    "crawl_site",
    "Crawl a URL with Firecrawl (robust on JS-heavy pages) into clean markdown + links, "
    "saved to output/<site>/crawl.md. Use for the 'crawl every page' step. Requires "
    "FIRECRAWL_API_KEY; if unset, use extract_site (Playwright) instead.",
    {"url": str},
)
async def crawl_site(args: dict) -> dict:
    if not _firecrawl.available():
        return {"content": [{"type": "text", "text":
            "Firecrawl not configured (FIRECRAWL_API_KEY unset). Use extract_site instead."}],
            "isError": True}
    url = args["url"]
    info = _firecrawl.scrape_to(url, OUTPUT / _slug(url))
    return {"content": [{"type": "text", "text":
        f"Crawled -> output/{_slug(url)}/crawl.md ({info['chars']} chars, "
        f"{info['links']} links). Title: {info['title']}"}]}


@tool(
    "research_competitors",
    "Semantic web search (Exa) for best-in-class ecommerce references + CRO/UX best practices "
    "for a category or brand. Use for 'research competitors / find better solutions'. Requires "
    "EXA_API_KEY.",
    {"query": str},
)
async def research_competitors(args: dict) -> dict:
    if not _exa.available():
        return {"content": [{"type": "text", "text":
            "Exa not configured (EXA_API_KEY unset). Use the built-in Reference Engine instead."}],
            "isError": True}
    results = _exa.research_competitors(args["query"])
    lines = [f"- {r['title']}\n  {r['url']}\n  {r['snippet'][:200]}" for r in results]
    return {"content": [{"type": "text", "text": "\n".join(lines) or "no results"}]}


def _mcp_server():
    return create_sdk_mcp_server(
        name="design_director",
        version="0.1.0",
        tools=[extract_site, crawl_site, research_competitors, run_slop_gate, get_references],
    )


# --------------------------------------------------------------- subagents ----

def _load_subagents() -> dict[str, AgentDefinition]:
    agents_dir = ROOT / "agents"
    specs = {
        "research":         ("1_research.md",        "Discovery & business research from real extracted data."),
        "ux_architect":     ("2_ux_architect.md",    "UX audit + information architecture (Baymard/NN-g)."),
        "ui_designer":      ("3_ui_designer.md",     "Builds one section in real HTML/CSS, grounded in real data."),
        "cro":              ("4_cro.md",             "Reviews a section for conversion + performance."),
        "platform":         ("5_platform.md",        "Shopify Plus / Magento implementability review."),
        "creative_director":("6_creative_director.md","FINAL approval authority; rejects AI-slop."),
    }
    out: dict[str, AgentDefinition] = {}
    for name, (fname, desc) in specs.items():
        prompt = (agents_dir / fname).read_text(encoding="utf-8")
        out[name] = AgentDefinition(description=desc, prompt=prompt)
    return out


# ------------------------------------------------------------- build options ---

def _compose_system_prompt() -> str:
    """SYSTEM_PROMPT + the baked Design DNA + a pointer to the component library.
    This is what makes the agent NOT need to be told fonts/colours/'improve not copy'."""
    parts = [(ROOT / "SYSTEM_PROMPT.md").read_text(encoding="utf-8")]
    dna = ROOT / "knowledge" / "design_dna.md"
    if dna.exists():
        parts.append("\n\n# ===== BAKED DESIGN DNA (always apply) =====\n"
                      + dna.read_text(encoding="utf-8"))
    lib = ROOT / "knowledge" / "component_library.md"
    if lib.exists():
        parts.append(f"\n\n# Component library: READ `{lib}` and REUSE its working patterns "
                     "(premium header, working stitching+size+live-price, sticky add-to-cart, "
                     "offers pill, trust/spec/accordions) instead of rebuilding.")
    return "\n".join(parts)


def build_options(work_dir: str | None = None) -> ClaudeAgentOptions:
    prompt_file = CACHE / "director_system_prompt.md"
    prompt_file.write_text(_compose_system_prompt(), encoding="utf-8")

    return ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code"},
        extra_args={"append-system-prompt-file": str(prompt_file)},
        mcp_servers={"design_director": _mcp_server()},
        agents=_load_subagents(),
        allowed_tools=[
            "mcp__design_director__extract_site",
            "mcp__design_director__crawl_site",
            "mcp__design_director__research_competitors",
            "mcp__design_director__run_slop_gate",
            "mcp__design_director__get_references",
            "Task",  # REQUIRED to actually invoke the 6 subagents (synchronous)
            "Read", "Write", "Edit", "Glob", "Grep", "Bash", "TodoWrite",
        ],
        cwd=work_dir or str(ROOT),
        model="claude-opus-4-8",
    )


if __name__ == "__main__":
    # sanity check: build options and list what's wired
    opts = build_options()
    subs = _load_subagents()
    print("system prompt: SYSTEM_PROMPT.md loaded")
    print("subagents:", ", ".join(subs.keys()))
    print("mcp tools: extract_site, crawl_site(firecrawl), research_competitors(exa), "
          "run_slop_gate, get_references")
    print("firecrawl:", _firecrawl.available(), "| exa:", _exa.available(),
          "| brightData: set BRIGHTDATA_BROWSER_WSS or BRIGHTDATA_PROXY")
