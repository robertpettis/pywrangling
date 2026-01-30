"""
Beamer-style themes for Jupyter / RISE (Reveal.js) slides.

What this module does
---------------------
- Generates Beamer-inspired Reveal.js CSS themes (Copenhagen, Madrid, Warsaw,
  AnnArbor, Berkeley).
- Vendors Latin Modern (Computer-Modern-style) webfonts locally so slides
  look like Beamer.
- Works on Windows and Linux with no system font installation.
- Writes everything into the notebook working directory.

Typical usage
-------------
In a notebook located one level ABOVE the pywrangling package:

    from pywrangling.jupyter_slides_functions import create_beamer_rise_theme
    create_beamer_rise_theme("copenhagen")

This will create:
    rise.css
    beamer_assets/
        webfonts/
            latinmodern-roman.css
            fonts/*.woff2
        themes/
            beamer_copenhagen.css

RISE automatically loads rise.css when you start the slideshow.

Offline usage
-------------
If you cannot download fonts:
    create_beamer_rise_theme("copenhagen", skip_font_download=True)

and manually populate:
    beamer_assets/webfonts/latinmodern-roman.css
    beamer_assets/webfonts/fonts/*.woff2
"""

from __future__ import annotations

import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse


# =============================================================================
# Public API
# =============================================================================

def create_beamer_rise_theme(
    theme: str = "copenhagen",
    out_css: str = "rise.css",
    assets_dir: str = "beamer_assets",
    font_pack: str = "latin-modern",
    skip_font_download: bool = False,
) -> Path:
    """
    Create a Beamer-like Reveal.js/RISE theme in the current working directory.
    """
    theme_key = _normalize_theme(theme)

    root = Path.cwd()
    assets_root = root / assets_dir
    webfonts_root = assets_root / "webfonts"
    themes_root = assets_root / "themes"

    webfonts_root.mkdir(parents=True, exist_ok=True)
    themes_root.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Fonts
    # -------------------------------------------------------------------------
    font_css_path: Optional[Path] = None
    if font_pack.lower() == "latin-modern":
        if not skip_font_download:
            font_css_path = ensure_latin_modern_webfonts(webfonts_root)
        else:
            candidate = webfonts_root / "latinmodern-roman.css"
            if candidate.exists():
                font_css_path = candidate
    else:
        raise ValueError("Only font_pack='latin-modern' is supported.")

    # -------------------------------------------------------------------------
    # Theme CSS
    # -------------------------------------------------------------------------
    theme_css_path = themes_root / f"beamer_{theme_key}.css"
    theme_css_path.write_text(_theme_css(theme_key), encoding="utf-8")

    # -------------------------------------------------------------------------
    # Compose rise.css
    # -------------------------------------------------------------------------
    out_path = root / out_css
    composed_css = _compose_rise_css(
        font_css_rel=_rel_or_none(font_css_path, root),
        theme_css_rel=_rel_or_none(theme_css_path, root),
    )
    out_path.write_text(composed_css, encoding="utf-8")

    return out_path


def ensure_latin_modern_webfonts(webfonts_root: Path) -> Path:
    """
    Download Latin Modern webfont CSS + WOFF2 files and vendor them locally.

    Fixes:
    - Resolves relative URLs in the upstream CSS (e.g. ../font/...)
    - Only downloads modern formats (WOFF2; optionally WOFF)
    - Rewrites the vendored CSS to point at local ./fonts/<file>
    """
    webfonts_root = Path(webfonts_root)
    fonts_dir = webfonts_root / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    upstream_css_url = (
        "https://cdn.jsdelivr.net/gh/sugina-dev/latin-modern-web@1.0.1/style/latinmodern-roman.css"
    )

    vendored_css_path = webfonts_root / "latinmodern-roman.css"

    css_text = _download_text(upstream_css_url)

    # Extract urls from CSS, but keep only woff2 (and optionally woff)
    raw_urls = _extract_css_urls(css_text)
    filtered = [u for u in raw_urls if _is_font_asset_we_want(u)]

    url_map: Dict[str, str] = {}

    for u in filtered:
        # Resolve relative URL against the CSS URL
        abs_url = urljoin(upstream_css_url, u)

        local_name = _safe_basename(abs_url)
        local_path = fonts_dir / local_name

        if not local_path.exists():
            _download_file(abs_url, local_path)

        # Rewrite CSS references to local relative paths
        url_map[u] = f"./fonts/{local_name}"

    rewritten = css_text
    for src, dst in url_map.items():
        rewritten = rewritten.replace(src, dst)

    vendored_css_path.write_text(rewritten, encoding="utf-8")
    return vendored_css_path



# =============================================================================
# CSS generation
# =============================================================================

def _compose_rise_css(
    font_css_rel: Optional[str],
    theme_css_rel: Optional[str],
) -> str:
    parts: List[str] = []
    parts.append("/* Auto-generated Beamer-style RISE theme */\n")

    if font_css_rel:
        parts.append(f"@import url('{font_css_rel.replace(os.sep, '/')}');\n")

    if theme_css_rel:
        parts.append(f"@import url('{theme_css_rel.replace(os.sep, '/')}');\n")

    parts.append(_GLOBAL_BEAMER_CSS)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Global CSS shared across all themes – Beamer base layout
# ---------------------------------------------------------------------------
_GLOBAL_BEAMER_CSS = """
/* ===== Global Beamer base ===== */
.reveal {
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  font-size: 28px;
  line-height: 1.35;
  color: #000;
}

.reveal .slides {
  text-align: left;
}

.reveal .slides section {
  padding: 60px 40px 50px 40px;
  box-sizing: border-box;
  text-align: left;
  height: 100%;
}

.reveal h1, .reveal h2, .reveal h3 {
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  font-weight: bold;
  text-transform: none;
  letter-spacing: normal;
  word-spacing: normal;
}

.reveal pre, .reveal code {
  font-size: 0.85em;
}

.reveal .slide-number {
  font-size: 0.55em;
  padding: 0.15em 0.35em;
  border-radius: 3px;
}

/* ===== Beamer block environments ===== */
/* Use with HTML:
   <div class="beamer-block">
     <div class="block-title">Remark</div>
     <div class="block-body">Sample text</div>
   </div>
*/
.beamer-block {
  margin: 0.6em 0;
  border-radius: 6px 6px 0 0;
  overflow: hidden;
}

.beamer-block .block-title {
  padding: 0.25em 0.7em;
  font-weight: bold;
  color: #fff;
  font-size: 0.95em;
  border-radius: 6px 6px 0 0;
}

.beamer-block .block-body {
  padding: 0.4em 0.7em;
  font-size: 0.95em;
}

/* Default block (blue/structure) */
.beamer-block .block-title {
  background: var(--bm-block-bg, #2D2D85);
}
.beamer-block .block-body {
  background: var(--bm-block-body-bg, #DDDDE8);
}

/* Alert block (red) */
.beamer-block.alert .block-title {
  background: var(--bm-alert-bg, #A00000);
}
.beamer-block.alert .block-body {
  background: var(--bm-alert-body-bg, #F2DEDE);
}

/* Example block (green) */
.beamer-block.example .block-title {
  background: var(--bm-example-bg, #006000);
}
.beamer-block.example .block-body {
  background: var(--bm-example-body-bg, #DEF0DE);
}

/* ===== Highlighted text ===== */
.beamer-highlight {
  color: #C00000;
  font-weight: bold;
}

/* ===== Beamer title slide ===== */
.beamer-title-box {
  background: var(--bm-structure, #2D2D85);
  color: #fff;
  padding: 0.5em 1em;
  border-radius: 8px;
  text-align: center;
  margin: 0.5em auto;
  max-width: 80%;
}

.beamer-title-box h1,
.beamer-title-box h2 {
  color: #fff !important;
  margin: 0.1em 0;
  background: none !important;
  border: none !important;
  text-align: center;
}

.beamer-title-box .subtitle {
  font-size: 0.8em;
  margin-top: 0.2em;
}

.beamer-authors {
  text-align: center;
  margin-top: 1em;
  font-size: 0.9em;
}

.beamer-institutes {
  text-align: center;
  font-size: 0.75em;
  margin-top: 0.5em;
  color: #444;
}

.beamer-date {
  text-align: center;
  font-size: 0.8em;
  margin-top: 0.8em;
}

.beamer-logo {
  position: fixed;
  bottom: 40px;
  right: 12px;
  z-index: 1002;
  width: 50px;
  height: 50px;
}

.beamer-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* ===== Beamer footer bar ===== */
.beamer-footline {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 28px;
  display: flex;
  align-items: center;
  z-index: 1001;
  font-size: 11px;
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  color: #fff;
}

.beamer-footline .foot-left,
.beamer-footline .foot-center,
.beamer-footline .foot-right {
  padding: 0 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 28px;
}

/* ===== Beamer header bar ===== */
.beamer-headline {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 36px;
  z-index: 1001;
  display: flex;
  align-items: center;
  font-size: 12px;
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  color: #fff;
}

.beamer-headline .head-left,
.beamer-headline .head-right {
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 16px;
}

/* ===== Navigation dots (mimics Beamer miniframes) ===== */
.beamer-nav-dots {
  display: inline-flex;
  gap: 4px;
  margin-left: 8px;
}

.beamer-nav-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  display: inline-block;
}

.beamer-nav-dots .dot.active {
  background: #fff;
}
"""


def _theme_css(theme_key: str) -> str:
    """Return theme-specific CSS for a given Beamer theme."""

    # =====================================================================
    # Copenhagen
    # =====================================================================
    if theme_key == "copenhagen":
        return """
/* Copenhagen theme – outer: split, inner: rounded, colors: whale+orchid */
:root {
  --bm-structure: #2D2D85;
  --bm-structure-dark: #1A1A5E;
  --bm-structure-darker: #0D0D3B;

  /* Block colors (orchid) */
  --bm-block-bg: #2D2D85;
  --bm-block-body-bg: #DDDDE8;
  --bm-alert-bg: #A00000;
  --bm-alert-body-bg: #F2DEDE;
  --bm-example-bg: #006000;
  --bm-example-body-bg: #DEF0DE;
}

/* --- Header bar (split outer theme) --- */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-structure) 0%, var(--bm-structure) 50%,
    var(--bm-structure-dark) 50%, var(--bm-structure-dark) 100%
  );
  z-index: 1000;
}

/* --- Footer bar (split outer theme) --- */
.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%, var(--bm-structure-darker) 30%,
    var(--bm-structure-dark) 30%, var(--bm-structure-dark) 65%,
    var(--bm-structure) 65%, var(--bm-structure) 100%
  );
  z-index: 1000;
}

/* --- Slide title --- */
.reveal h2 {
  color: #fff;
  position: relative;
  z-index: 1001;
  margin: 0;
  padding: 0.15em 0.4em;
  font-size: 1.15em;
  line-height: 40px;
  margin-top: -60px;
  margin-left: -40px;
  margin-right: -40px;
  padding-left: 40px;
}

/* Title slide h1 stays in content area */
.reveal h1 {
  color: #fff;
  font-size: 1.3em;
}

/* --- Slide content spacing below header --- */
.reveal .slides section {
  padding-top: 56px;
  padding-bottom: 44px;
}

/* --- Slide number --- */
.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px;
  right: 8px;
  z-index: 1002;
}

/* Title box on title slide */
.beamer-title-box {
  background: var(--bm-structure);
  border-radius: 8px;
}
"""

    # =====================================================================
    # Madrid
    # =====================================================================
    if theme_key == "madrid":
        return """
/* Madrid theme – outer: infolines, inner: rounded, colors: whale+orchid */
:root {
  --bm-structure: #2D2D85;
  --bm-structure-dark: #1A1A5E;
  --bm-structure-darker: #0D0D3B;

  --bm-block-bg: #2D2D85;
  --bm-block-body-bg: #DDDDE8;
  --bm-alert-bg: #A00000;
  --bm-alert-body-bg: #F2DEDE;
  --bm-example-bg: #006000;
  --bm-example-body-bg: #DEF0DE;
}

/* --- Header bar (infolines outer theme) --- */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%, var(--bm-structure-darker) 33%,
    var(--bm-structure-dark) 33%, var(--bm-structure-dark) 66%,
    var(--bm-structure) 66%, var(--bm-structure) 100%
  );
  z-index: 1000;
}

/* --- Footer bar (infolines) --- */
.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%, var(--bm-structure-darker) 33%,
    var(--bm-structure-dark) 33%, var(--bm-structure-dark) 66%,
    var(--bm-structure) 66%, var(--bm-structure) 100%
  );
  z-index: 1000;
}

/* --- Slide title --- */
.reveal h2 {
  background: var(--bm-structure);
  color: #fff;
  padding: 0.2em 0.6em;
  border-radius: 6px;
  font-size: 1.15em;
  margin-bottom: 0.5em;
}

.reveal h1 {
  color: #fff;
  font-size: 1.3em;
}

.reveal .slides section {
  padding-top: 56px;
  padding-bottom: 44px;
}

.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px;
  right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-structure);
  border-radius: 8px;
}
"""

    # =====================================================================
    # Warsaw
    # =====================================================================
    if theme_key == "warsaw":
        return """
/* Warsaw theme – outer: shadow, inner: rounded, colors: whale+orchid */
:root {
  --bm-structure: #2D2D85;
  --bm-structure-dark: #1A1A5E;
  --bm-structure-darker: #0D0D3B;

  --bm-block-bg: #2D2D85;
  --bm-block-body-bg: #DDDDE8;
  --bm-alert-bg: #A00000;
  --bm-alert-body-bg: #F2DEDE;
  --bm-example-bg: #006000;
  --bm-example-body-bg: #DEF0DE;
}

/* --- Header bar (shadow outer theme) --- */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 44px;
  background: linear-gradient(
    to bottom,
    var(--bm-structure) 0%, var(--bm-structure) 85%,
    var(--bm-structure-dark) 100%
  );
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  z-index: 1000;
}

/* --- Footer bar --- */
.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%, var(--bm-structure-darker) 33%,
    var(--bm-structure-dark) 33%, var(--bm-structure-dark) 66%,
    var(--bm-structure) 66%, var(--bm-structure) 100%
  );
  z-index: 1000;
}

/* --- Frame title with shadow --- */
.reveal h2 {
  background: linear-gradient(to bottom, var(--bm-structure), var(--bm-structure-dark));
  color: #fff;
  padding: 0.25em 0.6em;
  border-radius: 6px;
  font-size: 1.15em;
  box-shadow: 0 2px 4px rgba(0,0,0,0.25);
  margin-bottom: 0.5em;
}

.reveal h1 {
  color: #fff;
  font-size: 1.3em;
}

.reveal .slides section {
  padding-top: 60px;
  padding-bottom: 44px;
}

.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px;
  right: 8px;
  z-index: 1002;
}

/* Blocks get shadow too */
.beamer-block {
  box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

.beamer-title-box {
  background: linear-gradient(to bottom, var(--bm-structure), var(--bm-structure-dark));
  border-radius: 8px;
  box-shadow: 0 3px 6px rgba(0,0,0,0.25);
}
"""

    # =====================================================================
    # AnnArbor
    # =====================================================================
    if theme_key == "annarbor":
        return """
/* AnnArbor theme – outer: infolines, inner: rounded, colors: wolverine */
:root {
  --bm-blue: #002255;
  --bm-maize: #FFCB05;
  --bm-maize-dark: #E0A800;
  --bm-structure: #002255;

  --bm-block-bg: #002255;
  --bm-block-body-bg: #D6DCE4;
  --bm-alert-bg: #A00000;
  --bm-alert-body-bg: #F2DEDE;
  --bm-example-bg: #006000;
  --bm-example-body-bg: #DEF0DE;
}

/* --- Header bar (infolines) --- */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-blue) 0%, var(--bm-blue) 33%,
    var(--bm-maize-dark) 33%, var(--bm-maize-dark) 66%,
    var(--bm-maize) 66%, var(--bm-maize) 100%
  );
  z-index: 1000;
}

/* --- Footer bar (infolines) --- */
.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-blue) 0%, var(--bm-blue) 33%,
    var(--bm-maize-dark) 33%, var(--bm-maize-dark) 66%,
    var(--bm-maize) 66%, var(--bm-maize) 100%
  );
  z-index: 1000;
}

/* --- Frame title --- */
.reveal h2 {
  background: var(--bm-maize);
  color: #000;
  padding: 0.2em 0.55em;
  border-radius: 6px;
  font-size: 1.15em;
  margin-bottom: 0.5em;
}

.reveal h1 {
  color: #000;
  font-size: 1.3em;
}

.reveal .slides section {
  padding-top: 56px;
  padding-bottom: 44px;
}

.reveal .slide-number {
  background: var(--bm-blue);
  color: #fff;
  bottom: 4px;
  right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-maize);
  color: #000;
  border-radius: 8px;
}

.beamer-title-box h1,
.beamer-title-box h2 {
  color: #000 !important;
}
"""

    # =====================================================================
    # Berkeley
    # =====================================================================
    if theme_key == "berkeley":
        return """
/* Berkeley theme – outer: sidebar, inner: rectangles, colors: whale+orchid */
:root {
  --bm-structure: #2D2D85;
  --bm-structure-dark: #1A1A5E;
  --bm-sidebar-bg: #D8D8E8;

  --bm-block-bg: #2D2D85;
  --bm-block-body-bg: #DDDDE8;
  --bm-alert-bg: #A00000;
  --bm-alert-body-bg: #F2DEDE;
  --bm-example-bg: #006000;
  --bm-example-body-bg: #DEF0DE;
}

/* --- Sidebar (left panel) --- */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100px; height: 100%;
  background: var(--bm-structure);
  z-index: 1000;
}

/* --- Top bar spanning right of sidebar --- */
.reveal::after {
  content: "";
  position: fixed;
  top: 0; left: 100px;
  width: calc(100% - 100px); height: 36px;
  background: var(--bm-structure-dark);
  z-index: 1000;
}

.reveal .slides section {
  padding-left: 120px;
  padding-top: 52px;
  padding-bottom: 20px;
}

.reveal h2 {
  color: var(--bm-structure);
  border-bottom: 3px solid var(--bm-structure);
  font-size: 1.15em;
  padding-bottom: 0.15em;
  margin-bottom: 0.5em;
}

.reveal h1 {
  color: var(--bm-structure);
  font-size: 1.3em;
}

.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px;
  right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-structure);
  border-radius: 0;
}
"""

    raise ValueError(f"Unknown theme '{theme_key}'.")


# =============================================================================
# Helper utilities
# =============================================================================

_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)

def _is_font_asset_we_want(url: str) -> bool:
    """
    Keep only modern font formats we actually want to download.
    """
    u = url.lower().split("?")[0].split("#")[0]
    return u.endswith(".woff2") or u.endswith(".woff")

def _extract_css_urls(css_text: str) -> List[str]:
    urls: List[str] = []
    for m in _URL_RE.finditer(css_text):
        u = (m.group(2) or "").strip()
        if not u or u.startswith("data:"):
            continue
        urls.append(u)

    seen = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _safe_basename(url_or_path: str) -> str:
    base = url_or_path.split("/")[-1]
    base = base.split("?")[0].split("#")[0]
    return base or "asset.woff2"



def _download_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "jupyter-slides-beamer/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def _download_file(url: str, dest: Path, timeout: int = 60) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "jupyter-slides-beamer/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dest.write_bytes(r.read())


def _rel_or_none(path: Optional[Path], root: Path) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def _normalize_theme(theme: str) -> str:
    t = (theme or "").strip().lower()
    aliases = {
        "copenhagen": "copenhagen",
        "madrid": "madrid",
        "warsaw": "warsaw",
        "annarbor": "annarbor",
        "ann arbor": "annarbor",
        "berkeley": "berkeley",
    }
    if t not in aliases:
        raise ValueError(f"Unknown theme '{theme}'.")
    return aliases[t]


__all__ = [
    "create_beamer_rise_theme",
    "ensure_latin_modern_webfonts",
]
