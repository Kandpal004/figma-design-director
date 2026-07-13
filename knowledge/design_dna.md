# DESIGN DNA — the permanent house style (baked, never ask the user for this)

This is your locked design identity. The user must NOT have to specify fonts, colours,
spacing, or "make it premium / don't copy" every time — it is all here. Apply it by default.

## 0. THE MANDATE: AUDIT → IMPROVE, never clone
When given a reference or an existing page, you do NOT reproduce it 1:1. You rebuild a
**better** version:
- Upgrade the typography to the house fonts (below). A reference using Open Sans/system-ui/
  Lato is a weakness to FIX, not copy.
- Tighten the visual hierarchy and spacing to an 8pt grid.
- Add the CRO layer: sticky add-to-cart, trust cues, clear single primary CTA, urgency where
  honest, micro-interactions.
- Keep the reference's DATA and business intent (real prices, options, copy, images) — improve
  the CRAFT around it.
State, per section, one line: "Kept: <data>. Improved: <what and why>."

## 1. Type system (premium + READABLE — never negotiate)
- **Brand wordmark ONLY:** `Playfair Display` (700) — the ANDAAZ logo. Do NOT use Playfair for
  product titles, prices, or section headings (serif there reads dated / poor width use).
- **Everything else — product title, prices, headings, UI, body, labels, nav, buttons:**
  `Hanken Grotesk`. Product title = 700 (~30px, tight tracking); prices = 700.
  Highly readable premium grotesque. (Jost was too thin/geometric — read as AI + low
  readability. Do NOT use Jost/Lato.)
- **Body text minimum weight is 400** (never 300 for real content). Secondary text uses the
  `--ink-2` colour, NOT `--muted`, so it stays readable. `--muted` only for the faintest hints.
- **BANNED as the primary font (AI tells):** Inter, Roboto, Arial, Poppins, Montserrat,
  Open Sans, Lato, Jost, Geist, Space Grotesk, system-ui. If the real site uses one, replace it.
- Type scale (8pt-based): 12, 13, 14, 15, 16, 20, 24, 29, 36. Letter-spacing on uppercase
  nav/labels (.12-.18em). Line-height 1.24 for titles, 1.55-1.7 for body. Min body size 13px.

## 2. Colour
- **Accent = the brand colour extracted from the real site** (for Andaaz: rani `#a10047`).
  Use it sparingly — CTAs, active states, one accent per view. A "whisper", not a flood.
- Ink `#1c1b1d`, secondary `#4c505b`, muted `#8a8f99`, hairline `#ececee`, field `#f5f5f7`,
  success `#1f7a4d`, paper `#ffffff`. Dark utility bars `#201c1d`.
- **NEVER** cream/beige/off-white backgrounds. White or true neutrals only.

## 3. Spacing & layout
- **8pt grid**: 4/8/12/16/20/24/32/40/48/56. Generous, intentional whitespace.
- Max content width ~1440px, 40px page gutters (desktop); 16–20px (mobile).
- Obvious hierarchy: one clear focal point per section.

## 4. Icons (sharp + premium)
- Line icons, `stroke-width:1.5–1.6`, `stroke-linecap:round; stroke-linejoin:round`, ~23px.
- Consistent set. No emoji as UI icons (except flags/decorative). Bag = conversion anchor
  may carry the accent badge.

## 5. Components — reuse the library, don't reinvent
Working, proven patterns live in `knowledge/component_library.md`. READ it and reuse:
premium header (editorial + retail variants), **working stitching option** (reveals size grid
+ height, live price recalc), **always-sticky add-to-cart bar**, size grid, offers pill,
add-ons, trust row, spec table, accordions. Wire real interactivity (selection + live price),
never dead buttons.

## 5a. Carousels / rails
Product rails (Complete the Look, Similar Products, Recently Viewed) are luxury-minimal:
exactly 4 WHOLE cards fit the row (no cut/partial peeking card), clean images (NO discount
badges, NO wishlist hearts), generous whitespace, refined name/price. Prev/next arrow controls
are **rounded-square** buttons (~8px radius), NOT circles. Arrows page by a full row width.

## 6. Anti-slop (auto-fail — fix before showing)
No banned fonts · no cream bg · no gradient/shadow/glassmorphism spam · no oversized radius
(<=16px) · no floating cards without purpose · **NO long dashes anywhere in visible copy — no
em-dash and no en-dash. Use commas, periods, or parentheses instead** (e.g. "Fabric only, no
stitching included."). No placeholder images on product/hero/gallery (use REAL extracted
images) · no "Dribbble/AI template" look. Run `run_slop_gate` and clear it.

## 6a. Gallery rule (first-fold + no overlapping overlays)
A **"More Colours"** control must OVERLAY the product image (**bottom-LEFT** of the main image)
and be visible in the desktop first fold, ABOVE the sticky add-to-cart bar (size the stage with
`height:calc(100vh - ~306px)` so its bottom clears the sticky bar). Never bury it below the
page. Colour swatches sit on the image, not at the page bottom.
**Overlays must not collide:** if a "Hover to Zoom" (or similar) hint is also on the image,
put it at the **bottom-RIGHT** (never centered) so it never overlaps the bottom-left More
Colours pill. Any two image overlays go on opposite corners with clear space between.

## 6c. Fine-print = plain text, not decorative boxes
Small helper/description notes (stitching description, hints, disclaimers) are **plain grey
text** (`#6b7280`, ~13.5px), NOT wrapped in a tinted box with an accent left-border. A
decorative accent box around fine print reads as AI-generated. Match the real source: when in
doubt, extract the real element's computed style (bg/border/radius/padding/color) and replicate
it exactly rather than "designing" it.

## 6b. Accordions = single-open + FULL-WIDTH
Product Details, Style & Fit Tips, Shipping & Returns, FAQs (and any similar) are ALL
collapsible accordion items in ONE group with **single-open behaviour** (opening one closes the
others). Use native `<details name="group">` on every item (Product Details `open` by default).
**This whole block is a FULL-WIDTH section BELOW the 2-column gallery+info** (a sibling of the
main PDP grid, NOT nested inside the right info column). The Product Details **spec is a
multi-column grid** (3 columns on desktop) that fills the width with hairline key/value rows and
generous column gaps — never a cramped/overlapping single narrow column. Same for
"Similar Products" / reviews: full-width sections below, not inside the info column.

## 7. Grounding (non-negotiable)
Real fonts→replaced with house fonts; real COLOURS/IMAGES/DATA/OPTIONS from extraction or the
user's codebase (e.g. the Andaaz Magento module `Andaaz\CatalogPdp`) — never fabricated.
Working behaviour (e.g. stitching price logic) must mirror the real source.

## 7a. Multi-state components — extract & VERIFY every state (no re-prompting)
For any option/toggle/tab/accordion with multiple states, extract EACH state's full behaviour
from the real source (click every option on the live page + read the template), implement all
of them, and VERIFY + PRESENT every state — not just one. Never show only the "interesting"
state; the user must not have to ask "what about the other options?".
Reference — Andaaz stitching (all 3 states, from the live Magento, complete):
- **Unstitched** (+$0): note "Fabric only, no stitching included. Perfect for custom tailoring
  at your own discretion." No size, no height.
- **Stitched** (+$15): reveals the full size grid (32..69 with surcharges) + height select. No note.
- **Custom Stitched** (+$15): note "Get a made-to-measure outfit. Customise every detail for
  your perfect fit." No size/height (customisation is via a "get help" flow, not an inline form).

## 8. Section-by-section, human-gated
Build ONE section, apply all of the above, self-check the slop gate, present it, and STOP for
the user's approve/reject. Their feedback should be high-level ("approve" / "hero needs more
drama") — NOT font/spacing corrections, because those are already handled here.
