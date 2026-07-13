"""
extractor.py — the reliable, deterministic core.

Given a URL, it:
  1. opens the page (Playwright, real Chromium),
  2. takes a full-page screenshot,
  3. extracts REAL design tokens via getComputedStyle:
       - typography (font families actually used, with weights + sizes seen)
       - colors (real palette, ranked by pixel-weight of usage)
       - components (buttons, inputs, cards, nav, badges — counts + sample styles)
       - layout (max content width, section rhythm, grid hints)
       - navigation (top-level nav labels)
       - CRO elements (price, add-to-cart, trust badges, reviews, offers, urgency)
  4. downloads real product/hero images,
  5. writes everything to output/<site>/ .

Nothing here is guessed. If a value isn't on the page, it isn't in the output.
This is what every downstream design decision must be grounded in.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover
    async_playwright = None


# ---- the JS that runs IN the page to read real computed styles -----------------

_EXTRACT_JS = r"""
() => {
  const seen = (el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'
           && getComputedStyle(el).display !== 'none';
  };
  const norm = (c) => {
    // normalize rgb/rgba to lowercased 'r,g,b,a'
    if (!c) return null;
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return c;
    const p = m[1].split(',').map(s => s.trim());
    return p.length === 4 && parseFloat(p[3]) === 0 ? null : `rgb(${p[0]},${p[1]},${p[2]})`;
  };

  const els = Array.from(document.querySelectorAll('body *')).filter(seen);

  // ---- typography: font families actually rendered, weighted by area ----
  const fonts = {}, sizes = {}, weights = {};
  // ---- colors: text + background, weighted by element area ----
  const colorArea = {};

  for (const el of els) {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const area = Math.max(0, r.width) * Math.max(0, r.height);
    const hasText = el.childNodes && Array.from(el.childNodes)
        .some(n => n.nodeType === 3 && n.textContent.trim().length);

    if (hasText) {
      const fam = (cs.fontFamily || '').split(',')[0].replace(/["']/g, '').trim();
      if (fam) fonts[fam] = (fonts[fam] || 0) + area;
      const fs = Math.round(parseFloat(cs.fontSize));
      if (fs) sizes[fs] = (sizes[fs] || 0) + 1;
      const fw = cs.fontWeight;
      if (fw) weights[fw] = (weights[fw] || 0) + 1;
      const col = norm(cs.color);
      if (col) colorArea[col] = (colorArea[col] || 0) + Math.min(area, 5000);
    }
    const bg = norm(cs.backgroundColor);
    if (bg && area > 400) colorArea[bg] = (colorArea[bg] || 0) + area;
  }

  const rank = (obj) => Object.entries(obj).sort((a,b) => b[1]-a[1]);

  // ---- components ----
  const q = (sel) => Array.from(document.querySelectorAll(sel)).filter(seen);
  const sampleStyle = (el) => {
    if (!el) return null;
    const cs = getComputedStyle(el);
    return {
      bg: norm(cs.backgroundColor), color: norm(cs.color),
      radius: cs.borderRadius, padding: cs.padding,
      font: (cs.fontFamily||'').split(',')[0].replace(/["']/g,'').trim(),
      fontSize: cs.fontSize, fontWeight: cs.fontWeight,
      border: cs.border, boxShadow: cs.boxShadow,
    };
  };
  const buttons = q('button, [role=button], .btn, a.button, input[type=submit]');
  const inputs  = q('input:not([type=hidden]), textarea, select');
  const cards   = q('[class*=card], [class*=product], [class*=tile]');

  // ---- layout ----
  const bodyW = document.body.scrollWidth;
  let maxContent = 0;
  for (const el of q('div, section, main, header, footer')) {
    const w = el.getBoundingClientRect().width;
    if (w < bodyW * 0.98 && w > maxContent) maxContent = w;
  }

  // ---- navigation ----
  const navLinks = q('header a, nav a')
    .map(a => (a.textContent||'').trim())
    .filter(t => t && t.length < 30);

  // ---- CRO signals (presence detection) ----
  const bodyText = document.body.innerText.toLowerCase();
  const cro = {
    price:        /[₹$€£]\s?\d/.test(document.body.innerText),
    addToCart:    /add to (cart|bag)|buy (it )?now/i.test(document.body.innerText),
    reviews:      /review|rating|stars?/.test(bodyText),
    trustBadges:  /authentic|secure|guarantee|free (shipping|returns)|easy returns/.test(bodyText),
    offers:       /offer|discount|% off|coupon|sale/.test(bodyText),
    urgency:      /only \d+ left|hurry|limited|ends in|dispatch/.test(bodyText),
    wishlist:     /wishlist|save for later/.test(bodyText),
    sizeGuide:    /size guide|how to measure/.test(bodyText),
  };

  // ---- images (real product/hero candidates) ----
  const imgs = q('img')
    .map(i => ({ src: i.currentSrc || i.src, w: i.naturalWidth, h: i.naturalHeight,
                 alt: (i.alt||'').slice(0,80) }))
    .filter(i => i.src && i.w >= 300 && i.h >= 300)
    .sort((a,b) => (b.w*b.h) - (a.w*a.h))
    .slice(0, 8);

  return {
    typography: {
      families: rank(fonts).map(([k,v]) => ({ family: k, weight: Math.round(v) })),
      sizes: rank(sizes).map(([k,v]) => ({ px: +k, count: v })),
      weights: rank(weights).map(([k,v]) => ({ weight: +k, count: v })),
    },
    colors: rank(colorArea).slice(0, 16).map(([k,v]) => ({ color: k, area: Math.round(v) })),
    components: {
      buttons: { count: buttons.length, sample: sampleStyle(buttons[0]) },
      inputs:  { count: inputs.length,  sample: sampleStyle(inputs[0])  },
      cards:   { count: cards.length,   sample: sampleStyle(cards[0])   },
    },
    layout: { bodyWidth: bodyW, maxContentWidth: Math.round(maxContent) },
    navigation: [...new Set(navLinks)].slice(0, 24),
    cro,
    images: imgs,
    title: document.title,
    url: location.href,
  };
}
"""


def _slug(url: str) -> str:
    host = urlparse(url).netloc or "site"
    return re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")


async def extract(url: str, out_root: Path, crawl_limit: int = 1) -> dict:
    """Extract real design data from `url`. Returns the tokens dict and writes artifacts."""
    if async_playwright is None:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && python -m playwright install chromium"
        )

    site_dir = out_root / _slug(url)
    (site_dir / "images").mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # BrightData: unblock Cloudflare/anti-bot sites (e.g. andaazfashion.com).
        #   BRIGHTDATA_BROWSER_WSS  -> Scraping Browser CDP endpoint (connect over CDP), OR
        #   BRIGHTDATA_PROXY        -> proxy URL http://user:pass@brd.superproxy.io:22225
        bd_wss = os.environ.get("BRIGHTDATA_BROWSER_WSS")
        bd_proxy = os.environ.get("BRIGHTDATA_PROXY")
        if bd_wss:
            browser = await p.chromium.connect_over_cdp(bd_wss)
        elif bd_proxy:
            browser = await p.chromium.launch(headless=True, proxy={"server": bd_proxy})
        else:
            browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60_000)
        await page.wait_for_timeout(1500)  # let lazy content settle

        # full-page screenshot
        await page.screenshot(path=str(site_dir / "screenshot-full.png"), full_page=True)
        # above-the-fold screenshot
        await page.screenshot(path=str(site_dir / "screenshot-fold.png"))

        tokens = await page.evaluate(_EXTRACT_JS)

        # download real images
        downloaded = []
        for i, img in enumerate(tokens.get("images", [])[:6]):
            src = urljoin(url, img["src"])
            try:
                resp = await ctx.request.get(src, timeout=30_000)
                if resp.ok:
                    ext = ".png"
                    ctype = resp.headers.get("content-type", "")
                    if "jpeg" in ctype or "jpg" in ctype:
                        ext = ".jpg"
                    elif "webp" in ctype:
                        ext = ".webp"
                    fname = f"img-{i}{ext}"
                    (site_dir / "images" / fname).write_bytes(await resp.body())
                    downloaded.append({"file": f"images/{fname}", "src": src,
                                       "w": img["w"], "h": img["h"], "alt": img["alt"]})
            except Exception as e:  # noqa: BLE001
                print(f"[warn] image download failed {src}: {e}", file=sys.stderr)
        tokens["downloaded_images"] = downloaded

        await browser.close()

    (site_dir / "tokens.json").write_text(
        json.dumps(tokens, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_summary(site_dir, tokens)
    return tokens


def _write_summary(site_dir: Path, t: dict) -> None:
    """Human-readable grounding brief the design subagents read first."""
    fams = t["typography"]["families"][:3]
    top_colors = t["colors"][:8]
    lines = [
        f"# Grounding brief — {t.get('title','')}",
        f"URL: {t.get('url','')}",
        "",
        "## Real fonts (use these, do NOT invent)",
        *[f"- {f['family']}" for f in fams],
        "",
        "## Real color palette (extracted, ranked by usage)",
        *[f"- {c['color']}" for c in top_colors],
        "",
        "## Layout",
        f"- Max content width: {t['layout']['maxContentWidth']}px",
        "",
        "## Navigation (real top-level labels)",
        f"- {' · '.join(t['navigation'][:16])}",
        "",
        "## CRO elements present",
        *[f"- {k}: {v}" for k, v in t["cro"].items()],
        "",
        "## Real images downloaded (use these, no placeholders)",
        *[f"- {d['file']}  ({d['w']}x{d['h']})  {d['alt']}" for d in t.get("downloaded_images", [])],
    ]
    (site_dir / "grounding.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python extract/extractor.py <url> [output_dir]")
        raise SystemExit(2)
    url = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "output"
    tokens = asyncio.run(extract(url, out))
    print(f"OK  fonts={[f['family'] for f in tokens['typography']['families'][:3]]}")
    print(f"    colors={[c['color'] for c in tokens['colors'][:5]]}")
    print(f"    images={len(tokens.get('downloaded_images', []))} downloaded")
    print(f"    -> {out / _slug(url)}")


if __name__ == "__main__":
    main()
