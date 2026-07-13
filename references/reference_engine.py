"""
reference_engine.py — picks category-appropriate PREMIUM benchmark brands.

The agent never chooses references randomly (that's how you get an Apple + Amazon +
Gymshark mush). It detects the product category from the extracted data, then returns a
curated set of best-in-class brands to *calibrate craftsmanship against* — never to copy.

Detection is keyword-based over the site's real title / nav / body signals (from
extract/tokens.json), so the choice is grounded, not guessed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Reference:
    category: str
    brands: list[str]
    craft_notes: str


# curated premium benchmarks per category (calibration targets, not copy sources)
_CATALOG: dict[str, Reference] = {
    "fashion": Reference(
        "fashion",
        ["COS", "Zara", "Gymshark", "Alo Yoga", "Nike", "Aritzia"],
        "Editorial imagery, restrained type, generous whitespace, confident hierarchy.",
    ),
    "ethnic-fashion": Reference(
        "ethnic-fashion",
        ["Sabyasachi", "Fabindia", "Manyavar", "Nykaa Fashion", "Aritzia", "COS"],
        "Rich imagery + calm chrome; let the garment be the hero; premium serif accents.",
    ),
    "beauty": Reference(
        "beauty",
        ["Rhode", "Rare Beauty", "Glossier", "Sephora", "Ritual"],
        "Soft precise palette, big product photography, trust + ingredient transparency.",
    ),
    "jewellery": Reference(
        "jewellery",
        ["Mejuri", "Missoma", "Cartier", "Tiffany & Co."],
        "Lots of negative space, macro product shots, quiet luxury, thin elegant type.",
    ),
    "electronics": Reference(
        "electronics",
        ["Apple", "Nothing", "Dyson", "Sony", "Bose"],
        "Spec clarity, bold hero, monochrome discipline, motion used sparingly.",
    ),
    "supplements": Reference(
        "supplements",
        ["AG1", "Huel", "Ritual", "Transparent Labs"],
        "Trust-first, evidence + reviews, clean nutrition tables, confident CTAs.",
    ),
    "furniture": Reference(
        "furniture",
        ["Article", "HAY", "Muuto", "West Elm"],
        "Room-context imagery, calm palette, editorial grid, tactile detail shots.",
    ),
    "luxury": Reference(
        "luxury",
        ["Apple", "Rimowa", "Bang & Olufsen", "Bottega Veneta"],
        "Extreme restraint, huge whitespace, one hero idea per view.",
    ),
    "generic": Reference(
        "generic",
        ["Apple", "Nike", "COS", "Bellroy"],
        "Fall back to universally strong craft: spacing, hierarchy, restraint.",
    ),
}

# keyword -> category
_SIGNALS: dict[str, list[str]] = {
    "ethnic-fashion": ["saree", "salwar", "kameez", "lehenga", "kurta", "kurti", "ethnic",
                        "bridal", "anarkali", "sherwani", "dupatta", "indo western", "andaaz"],
    "fashion": ["dress", "apparel", "clothing", "outfit", "wear", "shirt", "jeans",
                "activewear", "fashion", "shoes", "sneaker"],
    "beauty": ["beauty", "skincare", "makeup", "serum", "cosmetic", "lipstick", "fragrance"],
    "jewellery": ["jewellery", "jewelry", "ring", "necklace", "earring", "gold", "diamond"],
    "electronics": ["phone", "laptop", "headphone", "speaker", "camera", "gadget",
                    "electronics", "charger", "earbuds"],
    "supplements": ["protein", "supplement", "vitamin", "nutrition", "wellness", "greens"],
    "furniture": ["furniture", "sofa", "couch", "chair", "table", "decor", "mattress"],
    "luxury": ["luxury", "premium", "couture", "haute", "atelier"],
}


def detect_category(tokens: dict) -> str:
    """Detect category from extracted tokens (title + nav + downloaded image alts)."""
    hay = " ".join([
        tokens.get("title", ""),
        " ".join(tokens.get("navigation", [])),
        " ".join(d.get("alt", "") for d in tokens.get("downloaded_images", [])),
        tokens.get("url", ""),
    ]).lower()

    scores = {cat: sum(hay.count(k) for k in kws) for cat, kws in _SIGNALS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "generic"


def references_for(tokens: dict) -> Reference:
    cat = detect_category(tokens)
    return _CATALOG.get(cat, _CATALOG["generic"])


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print("usage: python references/reference_engine.py <tokens.json>")
        raise SystemExit(2)
    tok = json.loads(open(sys.argv[1], encoding="utf-8").read())
    ref = references_for(tok)
    print(f"category: {ref.category}")
    print(f"benchmarks: {', '.join(ref.brands)}")
    print(f"craft: {ref.craft_notes}")
