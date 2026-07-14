# PROJECT STATE — read this first (handoff / memory)

This file is the synced project memory. Any laptop that pulls this repo (and any Claude Code
session opened here) should read this to understand where we are and how to continue.
Last updated: 2026-07-14.

## What this is
The **figma-design-director** agent (Python, Claude Agent SDK) audits a real ecommerce site,
extracts REAL design data, and rebuilds a higher-converting **premium** version section-by-section
with human approval. Target brand: **Andaaz Fashion** (premium ethnic wear). It must NOT look
AI-generated. Ground truth = the real Andaaz assets (see "Grounding" below).

## What has been built (all under output/andaaz-bvffgzb8fdewg8cq-z03-azurefd-net/sections/)
- **PDP** — `auto-product.html`: full product page (header, gallery + working stitching option w/
  live price, reviews + product-info 2-col, Complete-the-Look / Similar / Recently-Viewed rails,
  Watch&Shop shoppable reels, "Styled by Our Experts" dark concierge section, Customer Stories
  slider, grey footer, sticky add-to-cart bar).
- **Homepage** — `index.html` (ASSEMBLED single page, in order):
  1. utility bar + sticky header + **category strip** (12 real circular tiles, full-width, 1-line labels)
  2. **hero** (editorial split; model image on a rani-tint "Atelier" mat panel; "Woven for the moments…")
  3. **The Sale Edit** offer grid (4 cards: Salwar Suits/Lehengas/Sarees/Festive, "Up to 50% Off", Shop Now)
  4. **Shop by Collection** (Wedding / Festive / Ready to Ship)
  5. **New Arrivals** product rail (8 real products, arrows + drag)
  Individual section source files also exist: `home-hero.html`, `home-offergrid.html`,
  `home-collections.html`, `home-newarrivals.html`. `index.html` is the merged homepage.

## Live preview (Azure static website)
- URL root: **https://andaazpdpfigma.z29.web.core.windows.net/**
  - Homepage: `/sections/index.html`  · PDP: `/sections/auto-product.html`
- Hosted on: storage account **andaazpdpfigma**, resource group **rg-andaaz-demo**, sub *Vasansi-Production*.
- Redeploy after any change: run **`scripts/deploy-azure.bat`** (needs `az login`). It uploads the
  whole `output/andaaz-…/` folder to the `$web` container.

## Grounding — REAL Andaaz assets (never fabricate)
- Real site `andaazfashion.com` is Cloudflare-blocked to bots. Use the **mirror**:
  **https://andaaz-bvffgzb8fdewg8cq.z03.azurefd.net/** (accessible; homepage HTML + media).
- Real images already downloaded into `output/andaaz-…/`:
  - `home/category/tile-1..12.png` — the 12 category-strip thumbnails (real, w/ labels: Any 2 for $199,
    Best Seller, Wedding Dresses, Plus Size, Men Clothing, Saree, Indo-western, Pakistani Suits,
    Lehenga, Kids Collection, Trouser Suits, Jewellery).
  - `home/banner/hero1..3.jpg` — 3 model banners (red suit / pink lehenga / gold saree; 480x720).
  - `home/prod/{k1-8,l1-8,s1-11}.jpg` — 26 product shots (k=suits, l=lehengas, s=sarees; 480x720).
  - `images/img-0..5.jpg` (1200x1800 rani zari set) · `ctl/ctl-0..7.jpg` (480x720 cross-sell products).
  - Product data: `ctl-data.json` (real names/prices/was-prices). Tokens: `tokens.json`.
- To pull MORE real images, grep the mirror homepage HTML for `/media/andaaz/...\.(jpg|png)`.

## How to RUN the agent (it builds sections autonomously)
1. One-time per laptop: **`scripts/setup-runtime.bat`** (installs claude-agent-sdk + playwright + chromium).
2. `python agent/main.py "<high-level task>" "<expected_output_file>"`
   - The agent: reads real tokens/images/header → get_references + `research` subagent → builds ONE
     section grounded in real data → runs run_slop_gate → STOPS for approval. Do not have it build the
     whole page in one go.
3. Render/verify with a quick Playwright script (see `.cache/*.py` on the original laptop, gitignored —
   just write a small one: launch chromium, goto file:// URL, screenshot). Global `python` has playwright.
4. Slop gate: `python gates/slop_detector.py <file>` must PASS before shipping.

## THE WORKFLOW (important — this is how the user wants it)
- **Agent BUILDS whole sections** (research → grounded build → self-check). The user gives **HIGH-LEVEL**
  direction only ("build X", "more premium", "use a full-body image"), NOT pixel prompts.
- Recurring pixel/responsive rules are **baked into `knowledge/design_dna.md`** (esp. **§5b hero
  fold-fit + responsive**: JS fixed height = innerHeight − offsetTop, object-fit cover so portrait
  images crop not stretch, vh-scaled rhythm, medium-laptop + short-height breakpoints, plain eyebrow
  with NO decorative dash-line, verify at 1920/1440/1366/1180). If a fix recurs, BAKE it into the DNA
  so the agent gets it right next time — don't keep hand-fixing.
- Tiny one-off tweaks (a gap, a line-height) = quick hand-edit, not worth an agent round.

## Design DNA highlights (full detail in knowledge/design_dna.md)
- Fonts: **Hanken Grotesk only** (Playfair removed). Rani **#a10047** as a whisper (CTAs/active only).
- Never cream/beige bg. **No em/en-dashes** in visible copy (and no decorative dash-line before eyebrows).
- Real images only on hero/product slots. Luxury-minimal rails (4 whole cards, rounded-square arrows,
  no badges/hearts). Single-open full-width accordions. AUDIT → IMPROVE, never clone a competitor.

## User preferences & guardrails
- Communicates in **Hinglish**; respond in Hinglish.
- Wants to SEE the agent research/build (it does: reference engine + research subagent w/ Baymard/NN-g/
  Hick's-law citations). Show the research when relevant.
- Hero direction locked = **Style A split** (liked). REJECTED the cinematic full-bleed close-up
  (Style B / hero-3) — face-forward "beauty-ad" close-up felt wrong.
- Kalki is the competitor reference the user likes; audit → improve, do NOT clone (they called out a
  past Kalki clone as wrong).
- SECURITY (hard): **never use sampprati@vasansi.biz** (any email/mailbox). **Never commit secrets** —
  `.env`, keys, pems are gitignored; keep it that way.

## Git two-laptop sync
- Repo: `github.com/Kandpal004/figma-design-director` (branch main).
- `scripts/sync-push.bat` (auto-commit+push, every ~3 min via Task Scheduler here) /
  `scripts/sync-pull.bat` (auto-pull --rebase --autostash, every ~5 min on the other laptop).
- `output/` IS committed (HTML + images sync). `.env`, `.venv/`, `.cache/`, `.agent/` are NOT.

## Suggested next steps (not yet done)
- Homepage: a "Shop via Video Call / concierge" service banner (Kalki has one), testimonials, and a
  **footer** (reuse/adapt the PDP grey footer). Then assemble into `index.html`.
- Optional: move preview to a real domain; Figma import via html.to.design **browser extension**
  (the URL importer can't reach localhost; the Azure URL works for it).
