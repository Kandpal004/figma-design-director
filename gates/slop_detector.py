"""
slop_detector.py — the hard gate that stops "AI-generated looking" output.

Scans generated HTML/CSS for the tells that made every past attempt fail:
  - banned fonts (Inter/Roboto/Poppins/...)
  - placeholder images on product/hero/gallery slots (svg, data:, via.placeholder, gray box)
  - cream / beige "AI template" backgrounds
  - gradient / drop-shadow / glassmorphism spam
  - oversized border-radius
  - em-dash AI filler copy

Returns a list of Violation. An empty list means the section may be presented.
This is a BLOCK, not advice: the agent must fix violations before showing the user.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


BANNED_FONTS = {
    "inter", "roboto", "arial", "geist", "space grotesk", "poppins",
    "montserrat", "open sans", "helvetica neue", "nunito", "raleway",
}

# slots where a real image is mandatory (never a placeholder)
IMAGE_CRITICAL_HINTS = ("product", "hero", "gallery", "pdp", "banner", "media", "thumb")

PLACEHOLDER_SIGNS = (
    "via.placeholder", "placehold.co", "placeholder.com", "dummyimage",
    "data:image/svg", "unsplash.com/photos/random", "lorempixel", "picsum",
)


@dataclass
class Violation:
    kind: str
    detail: str
    severity: str = "block"  # block | warn


@dataclass
class Report:
    violations: list[Violation] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(v.severity == "block" for v in self.violations)

    def as_text(self) -> str:
        if not self.violations:
            return "PASS — no slop signals detected."
        out = ["SLOP GATE: " + ("BLOCKED" if self.blocked else "warnings only")]
        for v in self.violations:
            out.append(f"  [{v.severity}] {v.kind}: {v.detail}")
        return "\n".join(out)


def _is_cream(hex_or_rgb: str) -> bool:
    """Cream/beige/off-white AI-template background heuristic."""
    m = re.match(r"#([0-9a-fA-F]{6})", hex_or_rgb)
    if m:
        r, g, b = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    else:
        m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", hex_or_rgb)
        if not m:
            return False
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
    # warm, light, low-saturation off-white
    return r >= 240 and g >= 228 and 200 <= b <= 235 and (r - b) >= 10 and (g - b) >= 4


def scan_text(html: str) -> Report:
    rep = Report()
    low = html.lower()

    # 1) banned fonts
    for m in re.finditer(r"font-family\s*:\s*([^;{}]+)", low):
        primary = m.group(1).split(",")[0].replace('"', "").replace("'", "").strip()
        if primary in BANNED_FONTS:
            rep.violations.append(Violation(
                "banned-font", f"'{primary}' is an AI-tell font; use the site's real font."))
    for f in BANNED_FONTS:
        if re.search(rf"family=([^&\"']*){re.escape(f.replace(' ', '+'))}", low):
            rep.violations.append(Violation("banned-font-import", f"Google Fonts import of '{f}'."))

    # 2) placeholder images
    for sign in PLACEHOLDER_SIGNS:
        if sign in low:
            rep.violations.append(Violation("placeholder-image", f"placeholder source '{sign}'."))
    # svg/data-uri used on an image-critical slot
    for m in re.finditer(r'<img[^>]+>', low):
        tag = m.group(0)
        src = re.search(r'src\s*=\s*["\']([^"\']+)', tag)
        if not src:
            rep.violations.append(Violation("img-no-src", "an <img> has no src."))
            continue
        s = src.group(1)
        near = tag
        if (s.startswith("data:image/svg") or s.endswith(".svg")) and \
           any(h in near for h in IMAGE_CRITICAL_HINTS):
            rep.violations.append(Violation(
                "placeholder-on-critical", f"svg/placeholder on a product/hero/gallery img: {s[:60]}"))

    # 3) cream backgrounds
    for m in re.finditer(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6}|rgba?\([^)]+\))", low):
        if _is_cream(m.group(1)):
            rep.violations.append(Violation("cream-bg", f"cream/beige AI background {m.group(1)}."))

    # 4) gradient / shadow / glass spam (warn thresholds)
    grad = len(re.findall(r"linear-gradient|radial-gradient", low))
    if grad >= 4:
        rep.violations.append(Violation("gradient-spam", f"{grad} gradients — reduce.", "warn"))
    blur = len(re.findall(r"backdrop-filter\s*:\s*blur", low))
    if blur >= 2:
        rep.violations.append(Violation("glassmorphism", f"{blur} backdrop-blur uses.", "warn"))
    shadows = len(re.findall(r"box-shadow\s*:", low))
    if shadows >= 12:
        rep.violations.append(Violation("shadow-spam", f"{shadows} box-shadows — AI look.", "warn"))

    # 5) oversized radius
    for m in re.finditer(r"border-radius\s*:\s*(\d+)px", low):
        if int(m.group(1)) >= 32:
            rep.violations.append(Violation("oversized-radius", f"{m.group(1)}px radius.", "warn"))

    # 6) em-dash AI filler in visible copy (rough: many em dashes)
    if html.count("—") >= 4:
        rep.violations.append(Violation("em-dash-filler", "many em dashes — reads AI-written.", "warn"))

    return rep


def scan_file(path: str | Path) -> Report:
    return scan_text(Path(path).read_text(encoding="utf-8", errors="ignore"))


def scan_dir(root: str | Path) -> Report:
    root = Path(root)
    merged = Report()
    for f in list(root.rglob("*.html")) + list(root.rglob("*.css")):
        merged.violations.extend(scan_file(f).violations)
    return merged


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python gates/slop_detector.py <file-or-dir>")
        raise SystemExit(2)
    target = Path(sys.argv[1])
    report = scan_dir(target) if target.is_dir() else scan_file(target)
    print(report.as_text())
    raise SystemExit(1 if report.blocked else 0)
