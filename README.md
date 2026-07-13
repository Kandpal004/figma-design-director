# Figma Design Director

An AI **Ecommerce Design Director** that audits a real website, extracts its *real* design
data, and rebuilds a higher-converting version **section-by-section with human approval** —
then hands it to Figma.

It is **not** a "make a pretty design" bot. Its job is to think like a 25-year D2C
ecommerce Design Director + CRO + UX researcher, ground every decision in **real extracted
data** (never fabricated fonts/colors/images), block AI-slop with a hard gate, and require
the human Creative Director (you) to approve every section before moving on.

## Why this works (and the honest caveat)

Design quality comes from **4 things**, learned the hard way:
1. **Grounding in real data** — real fonts/colors/images/layout extracted from the live site.
2. **Anti-slop rules as a HARD gate** (not soft prompt text that gets diluted).
3. **Section-by-section human approval** — the Creative Director gate is load-bearing.
4. **Reference calibration** against category-appropriate premium brands.

The agent reliably produces an **85–90% grounded, non-slop scaffold**. The final 10–15%
"wow" comes from *your* approve/reject loop. This is a **human + AI** system, not autonomous
magic.

## Architecture (lean — no Postgres/Redis/Qdrant needed)

```
figma-design-director/
├── SYSTEM_PROMPT.md      # The Director brain: persona + non-AI rules + workflow
├── CLAUDE.md             # Behavior contract for the agent
├── agent/                # SDK wiring (options, hooks, subagent registry)
├── extract/              # Playwright: crawl + screenshots + REAL token extraction
├── agents/               # 6 subagent prompts (Research→UX→UI→CRO→Platform→Director)
├── gates/                # AI-slop detector (hard block) + section-approval gate
├── references/           # Reference Engine: category → premium benchmarks
├── knowledge/            # Baymard / NN-g / CRO / typography / spacing rules (RAG)
├── output/              # HTML/CSS + design-tokens JSON per section
└── tests/
```

## The pipeline

```
Input site → Crawl → Full-page screenshots → Extract REAL tokens
(typography, colors, components, layout, nav, CRO) → Detect weaknesses →
Competitor research → Improvement plan → [Creative Director approval] →
Build section → anti-slop gate → [approval] → next section → Figma export
```

## Figma export — the honest part

Native "AI writes an editable Figma file" is the weakest link, so we **don't build it** —
we reuse a mature MCP bridge:
- `grab/cursor-talk-to-figma-mcp` (6.9k⭐) — bidirectional Figma create/modify
- `dannote/figma-use` (578⭐) — full read/write for AI agents

The agent's own output is **HTML/CSS + a design-tokens JSON**; the MCP bridge turns that
into Figma. Requires your paid Figma seat.

## Status

🟡 Phase 1 — foundation. Building the Director brain first, then extraction, then gates.
