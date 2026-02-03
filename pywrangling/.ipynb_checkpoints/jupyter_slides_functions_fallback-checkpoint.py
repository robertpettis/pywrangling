"""
Beamer-style themes for Jupyter / RISE (Reveal.js) slides.

What this module does
---------------------
- Generates Beamer-inspired CSS themes (Copenhagen, Madrid, Warsaw,
  AnnArbor, Berkeley).
- Injects CSS directly into the notebook via IPython.display so it works
  immediately — no external rise.css file required.
- Also writes rise.css for RISE compatibility.
- Generates an nbconvert custom template so ``jupyter nbconvert --to slides``
  includes the Beamer CSS automatically.
- Vendors Latin Modern (Computer-Modern-style) webfonts locally so slides
  look like Beamer.
- Works on Windows and Linux with no system font installation.
- Writes asset files into the notebook working directory.

Typical usage
-------------
In a notebook cell:

    from pywrangling.jupyter_slides_functions import apply_beamer_theme
    apply_beamer_theme("copenhagen")

This will:
  1. Inject all CSS into the notebook immediately (works in both normal
     view and RISE slideshow).
  2. Write rise.css + beamer_assets/ for RISE auto-loading.
  3. Write beamer_assets/nbconvert_template/ for nbconvert slides export.

To export to HTML slides:

    jupyter nbconvert notebook.ipynb --to slides --template beamer_assets/nbconvert_template --post serve

To skip font downloading (offline):
    apply_beamer_theme("copenhagen", skip_font_download=True)
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

def apply_beamer_theme(
    theme: str = "copenhagen",
    out_css: str = "rise.css",
    assets_dir: str = "beamer_assets",
    font_pack: str = "latin-modern",
    skip_font_download: bool = False,
):
    """
    Apply a Beamer-like theme to the current Jupyter notebook.

    Injects CSS directly into the notebook output so that headers, footers,
    block environments, and all Beamer styling are visible immediately — both
    in normal notebook view and in RISE slideshow mode.

    Also writes rise.css for RISE auto-loading on slideshow launch.

    Parameters
    ----------
    theme : str
        One of: copenhagen, madrid, warsaw, annarbor, berkeley.
    out_css : str
        Filename for the RISE CSS file (default "rise.css").
    assets_dir : str
        Directory for vendored fonts and theme CSS files.
    font_pack : str
        Font pack to use (only "latin-modern" supported).
    skip_font_download : bool
        If True, skip downloading fonts (use previously downloaded ones).

    Returns
    -------
    IPython.display.HTML (auto-displayed in Jupyter) or Path if not in
    a notebook environment.
    """
    # Also write rise.css for RISE compatibility
    css_path = create_beamer_rise_theme(
        theme=theme,
        out_css=out_css,
        assets_dir=assets_dir,
        font_pack=font_pack,
        skip_font_download=skip_font_download,
    )

    # Build the full CSS to inject
    theme_key = _normalize_theme(theme)
    full_css = _theme_css(theme_key) + "\n" + _GLOBAL_BEAMER_CSS

    # Try to inject via IPython.display
    try:
        from IPython.display import HTML, display
        style_html = f"<style>\n{full_css}\n</style>"
        obj = HTML(style_html)
        display(obj)
        return obj
    except ImportError:
        # Not in a notebook — just return the path
        return css_path


def create_beamer_rise_theme(
    theme: str = "copenhagen",
    out_css: str = "rise.css",
    assets_dir: str = "beamer_assets",
    font_pack: str = "latin-modern",
    skip_font_download: bool = False,
) -> Path:
    """
    Create a Beamer-like Reveal.js/RISE theme in the current working directory.

    Writes rise.css and beamer_assets/ files. For direct notebook injection,
    use apply_beamer_theme() instead.
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

    # -------------------------------------------------------------------------
    # Generate nbconvert custom template for --to slides
    # -------------------------------------------------------------------------
    _write_nbconvert_template(assets_root, theme_key)

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
#
# Uses BOTH .reveal selectors (for RISE/Reveal.js) AND bare selectors
# (for normal notebook rendering) so styles appear in both modes.
# ---------------------------------------------------------------------------
_GLOBAL_BEAMER_CSS = r"""
/* ===== Global Beamer base ===== */

/* --- Font and base text --- */
.reveal,
.rendered_html,
.jp-RenderedHTMLCommon,
body {
  font-family: "Latin Modern Roman", "Computer Modern", "CMU Serif", serif;
  line-height: 1.35;
}

.reveal {
  font-size: 28px;
  color: #000;
}

.reveal .slides {
  text-align: left;
}

.reveal .slides section {
  padding: 60px 40px 50px 40px;
  box-sizing: border-box;
  text-align: left;
}

.reveal h1, .reveal h2, .reveal h3,
.rendered_html h1, .rendered_html h2, .rendered_html h3,
.jp-RenderedHTMLCommon h1, .jp-RenderedHTMLCommon h2, .jp-RenderedHTMLCommon h3 {
  font-family: "Latin Modern Roman", "Computer Modern", "CMU Serif", serif;
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
/*
  Usage in markdown cells:

  <div class="beamer-block">
    <div class="block-title">Remark</div>
    <div class="block-body">Sample text</div>
  </div>

  <div class="beamer-block alert">
    <div class="block-title">Important theorem</div>
    <div class="block-body">Sample text in red box</div>
  </div>

  <div class="beamer-block example">
    <div class="block-title">Examples</div>
    <div class="block-body">Sample text in green box.</div>
  </div>
*/

.beamer-block {
  margin: 0.7em 0;
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
  padding: 0.45em 0.7em;
  font-size: 0.95em;
  border: 1px solid rgba(0,0,0,0.08);
  border-top: none;
}

/* Default block (blue / structure colour) */
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
  padding: 0.5em 1.2em;
  border-radius: 8px;
  text-align: center;
  margin: 0.8em auto;
  max-width: 85%;
}

.beamer-title-box h1,
.beamer-title-box h2 {
  color: #fff !important;
  margin: 0.1em 0;
  background: none !important;
  border: none !important;
  text-align: center;
  padding: 0 !important;
  line-height: 1.3 !important;
  position: static !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}

.beamer-title-box .subtitle {
  font-size: 0.75em;
  margin-top: 0.3em;
  color: #e0e0ff;
}

.beamer-authors {
  text-align: center;
  margin-top: 1.2em;
  font-size: 0.9em;
}

.beamer-institutes {
  text-align: center;
  font-size: 0.72em;
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

/* ===== Beamer footer bar (HTML element version) ===== */
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

/* ===== Beamer header bar (HTML element version) ===== */
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



/* ===== Beamer-style itemize bullets ===== */

/* Disable default bullets */
.reveal ul,
.rendered_html ul,
.jp-RenderedHTMLCommon ul {
  list-style: none;
  padding-left: 1.2em;
}

/* Custom bullet */
.reveal ul li,
.rendered_html ul li,
.jp-RenderedHTMLCommon ul li {
  position: relative;
  margin: 0.35em 0;
}

/* Bullet glyph */
.reveal ul li::before,
.rendered_html ul li::before,
.jp-RenderedHTMLCommon ul li::before {
  content: "";
  position: absolute;
  left: -1.1em;
  top: 0.55em;

  width: 0.45em;
  height: 0.45em;
  border-radius: 50%;

  /* Glossy Beamer-style fill */
  background:
    radial-gradient(
      circle at 30% 30%,
      #ffffff 0%,
      var(--bm-structure, #2D2D85) 35%,
      var(--bm-structure-dark, #1A1A5E) 100%
    );

  /* Subtle depth */
  box-shadow:
    inset -0.04em -0.04em 0.06em rgba(0,0,0,0.35),
    0 0.03em 0.06em rgba(0,0,0,0.35);
}










"""


def _theme_css(theme_key: str) -> str:
    """Return theme-specific CSS for a given Beamer theme."""

    # =====================================================================
    # Copenhagen
    # =====================================================================
    if theme_key == "copenhagen":
        return r"""
/* Copenhagen theme – outer: split, inner: rounded, colors: whale+orchid */
:root {
  --bm-structure:        #2D2D85;
  --bm-structure-dark:   #1A1A5E;
  --bm-structure-darker: #0D0D3B;

  /* Block colours (orchid) */
  --bm-block-bg:         #2D2D85;
  --bm-block-body-bg:    #DDDDE8;
  --bm-alert-bg:         #A00000;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #006000;
  --bm-example-body-bg:  #DEF0DE;
}

/* ── Header bar (split outer theme) ── */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-structure) 0%,      var(--bm-structure) 50%,
    var(--bm-structure-dark) 50%, var(--bm-structure-dark) 100%
  );
  z-index: 1000;
}

/* ── Footer bar (split outer theme) ── */
.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 30%,
    var(--bm-structure-dark)  30%,  var(--bm-structure-dark)  65%,
    var(--bm-structure)       65%,  var(--bm-structure)       100%
  );
  z-index: 1000;
}

/* ── Slide title sits inside the header bar ── */
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

.reveal h1 {
  color: #fff;
  font-size: 1.3em;
}

/* ── Content area spacing ── */
.reveal .slides section {
  padding-top: 56px;
  padding-bottom: 44px;
}

/* ── Slide number ── */
.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px;
  right: 8px;
  z-index: 1002;
}

/* ── Title box on title slide ── */
.beamer-title-box {
  background: var(--bm-structure);
  border-radius: 8px;
}
"""

    # =====================================================================
    # Madrid
    # =====================================================================
    if theme_key == "madrid":
        return r"""
/* Madrid theme – outer: infolines, inner: rounded, colors: whale+orchid */
:root {
  --bm-structure:        #2D2D85;
  --bm-structure-dark:   #1A1A5E;
  --bm-structure-darker: #0D0D3B;

  --bm-block-bg:         #2D2D85;
  --bm-block-body-bg:    #DDDDE8;
  --bm-alert-bg:         #A00000;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #006000;
  --bm-example-body-bg:  #DEF0DE;
}

/* ── Header bar (infolines) ── */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 33%,
    var(--bm-structure-dark)   33%, var(--bm-structure-dark)   66%,
    var(--bm-structure)        66%, var(--bm-structure)        100%
  );
  z-index: 1000;
}

/* ── Footer bar (infolines) ── */
.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 33%,
    var(--bm-structure-dark)   33%, var(--bm-structure-dark)   66%,
    var(--bm-structure)        66%, var(--bm-structure)        100%
  );
  z-index: 1000;
}

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
  bottom: 4px; right: 8px;
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
        return r"""
/* Warsaw theme – outer: shadow, inner: rounded, colors: whale+orchid */
:root {
  --bm-structure:        #2D2D85;
  --bm-structure-dark:   #1A1A5E;
  --bm-structure-darker: #0D0D3B;

  --bm-block-bg:         #2D2D85;
  --bm-block-body-bg:    #DDDDE8;
  --bm-alert-bg:         #A00000;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #006000;
  --bm-example-body-bg:  #DEF0DE;
}

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

.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 33%,
    var(--bm-structure-dark)   33%, var(--bm-structure-dark)   66%,
    var(--bm-structure)        66%, var(--bm-structure)        100%
  );
  z-index: 1000;
}

.reveal h2 {
  background: linear-gradient(to bottom, var(--bm-structure), var(--bm-structure-dark));
  color: #fff;
  padding: 0.25em 0.6em;
  border-radius: 6px;
  font-size: 1.15em;
  box-shadow: 0 2px 4px rgba(0,0,0,0.25);
  margin-bottom: 0.5em;
}

.reveal h1 { color: #fff; font-size: 1.3em; }

.reveal .slides section {
  padding-top: 60px;
  padding-bottom: 44px;
}

.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px; right: 8px;
  z-index: 1002;
}

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
        return r"""
/* AnnArbor theme – outer: infolines, inner: rounded, colors: wolverine */
:root {
  --bm-blue:       #002255;
  --bm-maize:      #FFCB05;
  --bm-maize-dark: #E0A800;
  --bm-structure:  #002255;

  --bm-block-bg:         #002255;
  --bm-block-body-bg:    #D6DCE4;
  --bm-alert-bg:         #A00000;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #006000;
  --bm-example-body-bg:  #DEF0DE;
}

.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-blue)       0%,  var(--bm-blue)       33%,
    var(--bm-maize-dark) 33%, var(--bm-maize-dark)  66%,
    var(--bm-maize)      66%, var(--bm-maize)       100%
  );
  z-index: 1000;
}

.reveal::after {
  content: "";
  position: fixed;
  bottom: 0; left: 0;
  width: 100%; height: 28px;
  background: linear-gradient(
    to right,
    var(--bm-blue)       0%,  var(--bm-blue)       33%,
    var(--bm-maize-dark) 33%, var(--bm-maize-dark)  66%,
    var(--bm-maize)      66%, var(--bm-maize)       100%
  );
  z-index: 1000;
}

.reveal h2 {
  background: var(--bm-maize);
  color: #000;
  padding: 0.2em 0.55em;
  border-radius: 6px;
  font-size: 1.15em;
  margin-bottom: 0.5em;
}

.reveal h1 { color: #000; font-size: 1.3em; }

.reveal .slides section {
  padding-top: 56px;
  padding-bottom: 44px;
}

.reveal .slide-number {
  background: var(--bm-blue);
  color: #fff;
  bottom: 4px; right: 8px;
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
        return r"""
/* Berkeley theme – outer: sidebar, inner: rectangles, colors: whale+orchid */
:root {
  --bm-structure:      #2D2D85;
  --bm-structure-dark: #1A1A5E;
  --bm-sidebar-bg:     #D8D8E8;

  --bm-block-bg:         #2D2D85;
  --bm-block-body-bg:    #DDDDE8;
  --bm-alert-bg:         #A00000;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #006000;
  --bm-example-body-bg:  #DEF0DE;
}

.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100px; height: 100%;
  background: var(--bm-structure);
  z-index: 1000;
}

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

.reveal h1 { color: var(--bm-structure); font-size: 1.3em; }

.reveal .slide-number {
  background: var(--bm-structure);
  color: #fff;
  bottom: 4px; right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-structure);
  border-radius: 0;
}
"""

    raise ValueError(f"Unknown theme '{theme_key}'.")


# =============================================================================
# nbconvert template generation
# =============================================================================

def _write_nbconvert_template(assets_root: Path, theme_key: str) -> Path:
    """
    Generate a custom nbconvert template that inherits from the stock
    ``reveal`` template but injects our Beamer CSS.

    The template is written to ``assets_root/nbconvert_template/`` and can
    be used with::

        jupyter nbconvert nb.ipynb --to slides \\
            --template beamer_assets/nbconvert_template --post serve

    The template:
      - Extends the built-in ``reveal/index.html.j2``
      - Overrides ``html_head_css`` to inject theme + global Beamer CSS
      - Sets ``reveal_theme`` to ``white`` (minimal base that doesn't clash)
    """
    tpl_dir = assets_root / "nbconvert_template"
    tpl_dir.mkdir(parents=True, exist_ok=True)

    # --- conf.json tells nbconvert this template exists & inherits reveal ---
    conf = {
        "base_template": "reveal",
        "mimetypes": {
            "text/html": True
        }
    }
    import json
    (tpl_dir / "conf.json").write_text(
        json.dumps(conf, indent=2) + "\n", encoding="utf-8"
    )

    # --- Build the full CSS (theme-specific + global) ---
    full_css = _theme_css(theme_key) + "\n" + _GLOBAL_BEAMER_CSS

    # Escape Jinja delimiters in the CSS (unlikely but be safe)
    safe_css = full_css.replace("{%", "{%%").replace("%}", "%%}")

    # --- index.html.j2 extends the stock reveal template ---
    # We override body_header to inject our CSS AFTER the Reveal.js theme
    # link (which is at the end of <head>).  This ensures our Beamer styles
    # win the CSS cascade over white.css / simple.css.
    # We set reveal_theme to 'white' (the most minimal Reveal.js theme).
    template_content = (
        '{%- extends "reveal/index.html.j2" -%}\n'
        "\n"
        "{% set reveal_theme = 'white' %}\n"
        "\n"
        "{%- block body_header -%}\n"
        "{{ super() }}\n"
        "<style type=\"text/css\">\n"
        "/* === Beamer theme CSS (auto-generated) === */\n"
        f"{safe_css}\n"
        "</style>\n"
        "{%- endblock body_header -%}\n"
    )

    (tpl_dir / "index.html.j2").write_text(template_content, encoding="utf-8")

    return tpl_dir


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
    "apply_beamer_theme",
    "create_beamer_rise_theme",
    "ensure_latin_modern_webfonts",
]
