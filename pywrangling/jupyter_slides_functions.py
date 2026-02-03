"""
Beamer-style themes for Jupyter / RISE (Reveal.js) slides.

What this module does
---------------------
- Generates Beamer-inspired CSS themes (Copenhagen, Madrid, Warsaw,
  AnnArbor, Berkeley, Stanford, Gamecocks).
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
import json


# =============================================================================
# Public API
# =============================================================================

def apply_beamer_theme(
    theme: str = "madrid",
    skip_font_download: bool = False,
    *,
    author: str | None = None,
    date: str | None = None,
    logo_url: str | None = None,
    show_slide_number: bool = True,
    cell_tags: bool = False,
    notebook_path=None,
    lock_markdown: bool = False,
):
    """
    Apply a Beamer-like theme to Jupyter slides by injecting CSS + a JS "shell".

    IMPORTANT DESIGN (matches your requirement):
    - The header/footer content can come FROM EACH SLIDE.
    - Each slide may include an HTML metadata tag:

        <div class="beamer-meta"
             data-author="..."
             data-date="..."
             data-logo="...">
        </div>

      The JS reads the *current slide's* .beamer-meta tag (if present).
      If absent, it falls back to defaults passed into this function.

    Beamer-like layout:
    - Headline (top bar): optional logo + current slide title
    - Footline (bottom bar): author | date | slide_number/total

    Notes:
    - Designed for Reveal.js-based slides (RISE / JupyterLab RISE).
    - This *intentionally* reads metadata from slide HTML because rendered slides
      do not reliably preserve notebook-side state.
    """

    from IPython.display import display, HTML, Javascript

    css_path = create_beamer_rise_theme(theme=theme, skip_font_download=skip_font_download)

    # Read CSS as text and inject directly (works in notebook + RISE without relying on static file serving)
    css_text = Path(css_path).read_text(encoding="utf-8")

    # Normalize theme name for JS
    theme_key = _normalize_theme(theme)

    config = {
        "author": author or "",
        "date": date or "",
        "logo_url": logo_url or "",
        "show_slide_number": bool(show_slide_number),
        "lock_markdown": bool(lock_markdown),
        "theme": theme_key,
    }

    js = f"""
(function() {{
  const CONFIG = {json.dumps(config)};

  // ── Pen-tablet ghost-mouse suppressor ──
  // Tablets (Huion, Wacom, etc.) often emit BOTH pointer/pen events AND
  // synthesised mouse events for the same stroke.  The mouse coordinates
  // are slightly offset, causing the cursor to flicker between two
  // positions.  We suppress mouse events that arrive shortly after a
  // pen/stylus pointer event.
  (function() {{
    var lastPenTime = 0;
    var GRACE_MS = 400;  // ignore mouse events within this window

    // Track when a pen/stylus pointer event fires
    document.addEventListener("pointerdown", function(e) {{
      if (e.pointerType === "pen") lastPenTime = Date.now();
    }}, true);
    document.addEventListener("pointermove", function(e) {{
      if (e.pointerType === "pen") lastPenTime = Date.now();
    }}, true);

    // Block mouse events that follow a pen event (these are the ghosts)
    ["mousedown", "mousemove", "mouseup"].forEach(function(evtName) {{
      document.addEventListener(evtName, function(e) {{
        if (Date.now() - lastPenTime < GRACE_MS) {{
          e.stopPropagation();
          e.preventDefault();
        }}
      }}, true);  // capture phase — run before the chalkboard handler
    }});
  }})();

  // ── Hide RISE/Reveal UI controls by default; comma key toggles ──
  // Adds .beamer-hide-controls to <body> immediately so controls start
  // hidden.  Comma key (188) is set to null in Reveal.configure() so
  // Reveal passes it through, and we handle it here with e.repeat
  // filtering so it only toggles once per press.
  (function() {{
    document.body.classList.add("beamer-hide-controls");

    document.addEventListener("keydown", function(e) {{
      if ((e.key === "," || e.keyCode === 188) && !e.repeat) {{
        var tag = (e.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;
        document.body.classList.toggle("beamer-hide-controls");
      }}
    }}, true);
  }})();

  // ── Lock markdown cells during slideshow (prevent double-click editing) ──
  // When CONFIG.lock_markdown is true, intercept dblclick events on
  // markdown cells within .reveal .slides to prevent entering edit mode.
  (function() {{
    if (!CONFIG.lock_markdown) return;

    document.addEventListener("dblclick", function(e) {{
      // Only active when RISE/Reveal is showing
      var reveal = document.querySelector(".reveal");
      if (!reveal) return;

      // Check if click is inside a markdown cell within slides
      var target = e.target;
      var inSlides = false;
      var inMarkdown = false;
      var el = target;

      while (el && el !== document.body) {{
        if (el.classList && el.classList.contains("slides")) {{
          inSlides = true;
        }}
        // Classic Jupyter markdown cell: .text_cell, .rendered_html
        // JupyterLab: .jp-MarkdownCell
        if (el.classList && (
          el.classList.contains("text_cell") ||
          el.classList.contains("jp-MarkdownCell") ||
          (el.classList.contains("cell") && el.querySelector(".rendered_html"))
        )) {{
          inMarkdown = true;
        }}
        el = el.parentElement;
      }}

      if (inSlides && inMarkdown) {{
        e.stopPropagation();
        e.preventDefault();
      }}
    }}, true);  // capture phase
  }})();

  function firstHeadingText(section) {{
    if (!section) return "";
    // In nbconvert slides, headings have id attributes with anchor links.
    // In RISE, they're inside .rendered_html or .jp-RenderedHTMLCommon.
    // querySelector searches all descendants, so this handles both cases.
    var h = section.querySelector("h2, h3, h1");

    // If no heading in the current (sub-)section, check the parent section
    // (Reveal.js nests vertical slides inside a parent <section>).
    if (!h && section.parentElement && section.parentElement.tagName === "SECTION") {{
      h = section.parentElement.querySelector("h2, h3, h1");
    }}

    if (!h) return "";
    // Strip the pilcrow/anchor-link text that nbconvert appends
    var clone = h.cloneNode(true);
    var anchors = clone.querySelectorAll(".anchor-link");
    anchors.forEach(function(a) {{ a.remove(); }});
    return (clone.textContent || "").trim();
  }}

  function readSlideMeta(section) {{
    // Look for: <div class="beamer-meta" data-author="..." data-date="..." data-logo="..."></div>
    if (!section) return null;
    var meta = section.querySelector(".beamer-meta");
    if (!meta) return null;

    var author = meta.getAttribute("data-author");
    var date = meta.getAttribute("data-date");
    var logo = meta.getAttribute("data-logo");

    return {{
      author: (author !== null ? author : ""),
      date: (date !== null ? date : ""),
      logo: (logo !== null ? logo : ""),
    }};
  }}

  function ensureShell(revealEl) {{
    if (!revealEl) return null;

    revealEl.classList.add("beamer-shell");

    // -------------------------------
    // HEADLINE  — appended to document.body so no Reveal.js
    // transform on .reveal can break position:fixed.
    // -------------------------------
    var headline = document.querySelector(".beamer-headline");
    if (!headline) {{
      headline = document.createElement("div");
      headline.className = "beamer-headline";
      headline.innerHTML = `
        <div class="beamer-head-left"></div>
        <div class="beamer-head-title"></div>
      `;
      document.body.appendChild(headline);
    }}

    var headLeft = headline.querySelector(".beamer-head-left");
    var headTitle = headline.querySelector(".beamer-head-title");

    // -------------------------------
    // FOOTLINE  — also on document.body for the same reason.
    // -------------------------------
    var footline = document.querySelector(".beamer-footline");
    if (!footline) {{
      footline = document.createElement("div");
      footline.className = "beamer-footline";
      footline.innerHTML = `
        <div class="beamer-foot-left"></div>
        <div class="beamer-foot-center"></div>
        <div class="beamer-foot-right"></div>
      `;
      document.body.appendChild(footline);
    }}

    var footLeft = footline.querySelector(".beamer-foot-left");
    var footCenter = footline.querySelector(".beamer-foot-center");
    var footRight = footline.querySelector(".beamer-foot-right");

    // -------------------------------
    // BACKGROUND BARS — coloured bars behind headline/footline.
    // These replace the old .reveal::before/::after pseudo-elements
    // which broke under Reveal.js transforms.
    // -------------------------------
    if (!document.querySelector(".beamer-head-bg")) {{
      var headBg = document.createElement("div");
      headBg.className = "beamer-head-bg";
      document.body.appendChild(headBg);
    }}
    if (!document.querySelector(".beamer-foot-bg")) {{
      var footBg = document.createElement("div");
      footBg.className = "beamer-foot-bg";
      document.body.appendChild(footBg);
    }}

    // Hide Reveal.js's built-in slide number — we render our own.
    var builtinNum = revealEl.querySelector(".slide-number");
    if (builtinNum) {{
      builtinNum.style.display = "none";
    }}

    // Create our own slide-number span inside the footer.
    var customNum = footRight.querySelector(".beamer-slide-number");
    if (!customNum) {{
      customNum = document.createElement("span");
      customNum.className = "beamer-slide-number";
      footRight.appendChild(customNum);
    }}

    return {{
      headLeft: headLeft,
      headTitle: headTitle,
      footLeft: footLeft,
      footCenter: footCenter,
      footRight: footRight,
      slideNumber: customNum,
    }};
  }}

  function setLogo(headLeftEl, logoUrl) {{
    if (!headLeftEl) return;
    if (logoUrl && logoUrl.trim()) {{
      headLeftEl.innerHTML = `<img src="${{logoUrl}}" style="height:32px; width:auto; display:block;">`;
    }} else {{
      headLeftEl.innerHTML = "";
    }}
  }}



  function updateShell(revealEl, parts) {{
    try {{
      var currentSection = null;

      if (window.Reveal && typeof window.Reveal.getCurrentSlide === "function") {{
        currentSection = window.Reveal.getCurrentSlide();
      }} else {{
        currentSection = revealEl.querySelector("section.present") || null;
      }}

      // Title ALWAYS from the current slide heading.
      var title = firstHeadingText(currentSection);
      parts.headTitle.textContent = title;

      // Author/date/logo from slide meta if present, else defaults.
      var meta = readSlideMeta(currentSection);

      var author = (meta && meta.author !== "") ? meta.author : CONFIG.author;
      var date = (meta && meta.date !== "") ? meta.date : CONFIG.date;

      // For logo: slide meta overrides default *including allowing blank to hide logo*
      // If the slide explicitly includes data-logo="", it hides logo for that slide.
      var logo = null;
      if (meta && meta.logo !== null) {{
        logo = meta.logo; // may be "" (hide)
      }} else {{
        logo = CONFIG.logo_url;
      }}

      parts.footLeft.textContent = author || "";
      parts.footCenter.textContent = date || "";
      setLogo(parts.headLeft, logo);

      // Custom slide number: h.v/totalHorizontal (always show v, 1-based)
      if (CONFIG.show_slide_number && parts.slideNumber && window.Reveal) {{
        var idx = (typeof window.Reveal.getIndices === "function")
          ? window.Reveal.getIndices()
          : null;
        if (idx) {{
          var h = idx.h + 1;      // 1-based
          var v = idx.v + 1;      // 1-based
          // Count top-level <section> children = horizontal slide count
          var slidesEl = revealEl.querySelector(".slides");
          var totalH = slidesEl
            ? slidesEl.querySelectorAll(":scope > section").length
            : "?";
          parts.slideNumber.textContent = h + "." + v + "/" + totalH;
        }}
      }}

    }} catch (e) {{
      console.warn("beamer shell update failed:", e);
    }}
  }}

  function bootWhenReady() {{
    // RISE/JupyterLab RISE sometimes loads Reveal after DOM is ready.
    // So we retry until `.reveal` and `window.Reveal` exist.
    var tries = 0;
    var timer = setInterval(function() {{
      tries += 1;

      var revealEl = document.querySelector(".reveal");
      if (!revealEl) return;

      // We can still render shell even if Reveal isn't ready yet,
      // but slidechanged hooks require Reveal.
      var parts = ensureShell(revealEl);
      if (!parts) return;

      // If Reveal exists, hook events & stop retry loop.
      if (window.Reveal) {{
        // Enable slide numbers so Reveal.js creates the .slide-number element;
        // we overwrite its content with our custom format in updateShell().
        if (typeof window.Reveal.configure === "function") {{
          window.Reveal.configure({{
            slideNumber: true,
            // Disable touch/swipe navigation — it conflicts with the
            // chalkboard plugin's pen drawing, causing strokes to jerk
            // sideways as Reveal interprets them as slide-change swipes.
            touch: false,
            // Tell Reveal.js to pass comma key (188) through to the DOM
            // instead of swallowing it — our capture-phase keydown
            // listener handles the toggle with e.repeat filtering.
            keyboard: {{
              188: null
            }}
          }});
        }}

        updateShell(revealEl, parts);
// Reveal.js 4.x uses .on(), 3.x (RISE) uses .addEventListener()
        var bindEvent = (typeof window.Reveal.on === "function")
          ? function(evt, fn) {{ window.Reveal.on(evt, fn); }}
          : (typeof window.Reveal.addEventListener === "function")
            ? function(evt, fn) {{ window.Reveal.addEventListener(evt, fn); }}
            : null;

        if (bindEvent) {{
          bindEvent("slidechanged", function() {{
            updateShell(revealEl, parts);
}});
          bindEvent("ready", function() {{
            updateShell(revealEl, parts);
}});
        }}

        clearInterval(timer);
        return;
      }}

      // Even before Reveal is ready, try to update from "present" section.
      updateShell(revealEl, parts);

      // Fail-safe stop (don't loop forever)
      if (tries > 80) {{
        clearInterval(timer);
      }}
    }}, 150);
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", bootWhenReady);
  }} else {{
    bootWhenReady();
  }}
}})();
"""

    display(HTML(f"<style>{css_text}</style>"))
    display(Javascript(js))

    if cell_tags:
        apply_cell_tags(notebook_path=notebook_path)



def _build_inline_css_for_notebook(*, theme_key: str, assets_dir: str = "beamer_assets") -> str:
    """
    Build a single CSS string suitable for direct injection into a notebook/RISE.

    Why: rise.css uses @import statements that often fail to resolve in Jupyter,
    so the theme CSS (header/footer bars) never loads and the shell looks "missing".
    """
    root = Path.cwd()
    assets_root = root / assets_dir
    webfonts_root = assets_root / "webfonts"
    themes_root = assets_root / "themes"

    parts: List[str] = []

    # ---- Inline font CSS if it exists ----
    font_css_path = webfonts_root / "latinmodern-roman.css"
    if font_css_path.exists():
        font_css = font_css_path.read_text(encoding="utf-8", errors="replace")

        # Rewrite url('./fonts/<file>') to Jupyter-served /files/... path
        prefix = f"/files/{assets_dir}/webfonts/fonts/"
        font_css = re.sub(
            r"url\((['\"]?)(?:\./)?fonts/([^'\")]+)\1\)",
            lambda m: f"url({m.group(1)}{prefix}{m.group(2)}{m.group(1)})",
            font_css,
        )

        parts.append("/* === Vendored Latin Modern fonts (inline) === */\n")
        parts.append(font_css)
        parts.append("\n\n")

    # ---- Inline theme CSS (this is what paints the header/footer bars) ----
    theme_css_path = themes_root / f"beamer_{theme_key}.css"
    if theme_css_path.exists():
        parts.append("/* === Beamer theme CSS (inline) === */\n")
        parts.append(theme_css_path.read_text(encoding="utf-8", errors="replace"))
        parts.append("\n\n")

    # ---- Inline global CSS (positions .beamer-headline/.beamer-footline etc.) ----
    parts.append("/* === Global Beamer CSS (inline) === */\n")
    parts.append(_GLOBAL_BEAMER_CSS)

    return "".join(parts)


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
        theme_key=theme_key,
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
    theme_key: Optional[str] = None,
) -> str:
    """
    Compose the final rise.css with correct cascade order:
    1. Font CSS (import) - must come first per CSS spec
    2. Global CSS (inline) - base styles
    3. Theme CSS (inline) - theme-specific overrides

    This order ensures theme CSS can override global defaults without !important.
    """
    parts: List[str] = []
    parts.append("/* Auto-generated Beamer-style RISE theme */\n")

    # @import must come first in CSS
    if font_css_rel:
        parts.append(f"@import url('{font_css_rel.replace(os.sep, '/')}');\n")

    # Global base styles come first (can be overridden by theme)
    parts.append(_GLOBAL_BEAMER_CSS)

    # Theme-specific CSS comes last to override global defaults
    if theme_key:
        parts.append(f"\n/* ===== Theme: {theme_key} ===== */\n")
        parts.append(_theme_css(theme_key))

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
  font-size: 14px;
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  color: #fff;
  pointer-events: none;  /* don't intercept chalkboard drawing */
}

.beamer-footline .beamer-foot-left,
.beamer-footline .beamer-foot-center,
.beamer-footline .beamer-foot-right {
  flex: 1;
  padding: 0 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 28px;
}

.beamer-footline .beamer-foot-left {
  text-align: left;
}

.beamer-footline .beamer-foot-center {
  text-align: center;
}

.beamer-footline .beamer-foot-right {
  text-align: right;
}

/* ===== Beamer header bar (HTML element version) ===== */
.beamer-headline {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 40px;
  z-index: 1001;
  display: flex;
  align-items: center;
  font-size: 22px;
  font-weight: bold;
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  color: #fff;
  pointer-events: none;  /* don't intercept chalkboard drawing */
}

.beamer-headline .beamer-head-left {
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 12px;
}

.beamer-headline .beamer-head-title {
  flex: 1;
  padding: 0 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== Custom slide number inside .beamer-foot-right ===== */
.beamer-slide-number {
  font-family: "Latin Modern Roman", "Computer Modern", serif;
  font-size: 14px;
  color: #fff;
  line-height: 28px;
}

/* ===== Beamer-ish bullet markers (shiny dot) =====
   Beamer often uses a colored bullet with a subtle highlight.
   We fake that with a gradient overlay + tiny drop shadow.
*/
.reveal {
  --beamer-bullet: #0033A0;
}

.reveal ul,
.rendered_html ul,
.jp-RenderedHTMLCommon ul {
  list-style: none;
  padding-left: 1.2em;
}

.reveal ul li,
.rendered_html ul li,
.jp-RenderedHTMLCommon ul li {
  position: relative;
}

.reveal ul li::before,
.rendered_html ul li::before,
.jp-RenderedHTMLCommon ul li::before {
  content: "";
  position: absolute;
  left: -0.85em;
  top: 0.62em;               /* tuned for ~28–32px base text */
  width: 0.42em;
  height: 0.42em;
  border-radius: 999px;

  /* base color + highlight/shadow */
  background:
    radial-gradient(circle at 30% 30%, rgba(255,255,255,0.95), rgba(255,255,255,0.12) 35%, rgba(255,255,255,0.00) 60%),
    radial-gradient(circle at 70% 75%, rgba(0,0,0,0.22), rgba(0,0,0,0.00) 60%),
    var(--beamer-bullet);

  box-shadow: 0 0.06em 0.10em rgba(0,0,0,0.35);
}


/* Hide the in-slide heading when the JS header is active (we render it in the headline bar) */
.beamer-shell .slides section.present h1:first-child,
.beamer-shell .slides section.present h2:first-child,
.beamer-shell .slides section.present h3:first-child {
  display: none !important;
}

/* Jupyter often wraps rendered markdown; hide the first heading inside common wrappers too */
.beamer-shell .slides section.present .rendered_html h1:first-child,
.beamer-shell .slides section.present .rendered_html h2:first-child,
.beamer-shell .slides section.present .rendered_html h3:first-child,
.beamer-shell .slides section.present .jp-RenderedHTMLCommon h1:first-child,
.beamer-shell .slides section.present .jp-RenderedHTMLCommon h2:first-child,
.beamer-shell .slides section.present .jp-RenderedHTMLCommon h3:first-child {
  display: none !important;
}



/* Hide built-in Reveal numbering in all common placements */
.beamer-shell .slide-number,
.beamer-shell .reveal .slide-number,
.beamer-shell .reveal .slide-number-a,
.beamer-shell .reveal .slide-number-delimiter,
.beamer-shell .reveal .slide-number-b {
  display: none !important;
  visibility: hidden !important;
}

/* ===== Hide RISE / Reveal.js UI controls by default ===== */
/* Toggled visible with the comma key via JS.                */
/* Targets: RISE toolbar (exit X, help), chalkboard icons,   */
/* Reveal.js navigation arrows, and custom-controls.         */
body.beamer-hide-controls .reveal .slide-menu-button,
body.beamer-hide-controls #exit_b,
body.beamer-hide-controls #help_b,
body.beamer-hide-controls .chalkboard-button,
body.beamer-hide-controls .reveal .customcontrols,
body.beamer-hide-controls div.btn-group.rise-toolbar {
  opacity: 0 !important;
  pointer-events: none !important;
  transition: opacity 0.25s ease;
}

/* When controls are shown (class removed), fade them in */
body:not(.beamer-hide-controls) .reveal .slide-menu-button,
body:not(.beamer-hide-controls) #exit_b,
body:not(.beamer-hide-controls) #help_b,
body:not(.beamer-hide-controls) .chalkboard-button,
body:not(.beamer-hide-controls) .reveal .customcontrols,
body:not(.beamer-hide-controls) div.btn-group.rise-toolbar {
  opacity: 1 !important;
  pointer-events: auto !important;
  transition: opacity 0.25s ease;
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
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 40px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-structure) 0%,      var(--bm-structure) 50%,
    var(--bm-structure-dark) 50%, var(--bm-structure-dark) 100%
  );
}

.beamer-foot-bg {
  position: fixed;
  bottom: 0; left: 0;
  width: 100%;
  height: 28px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 30%,
    var(--bm-structure-dark)  30%,  var(--bm-structure-dark)  65%,
    var(--bm-structure)       65%,  var(--bm-structure)       100%
  );
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
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
  bottom: 0;
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
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 40px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 33%,
    var(--bm-structure-dark)   33%, var(--bm-structure-dark)   66%,
    var(--bm-structure)        66%, var(--bm-structure)        100%
  );
}

.beamer-foot-bg {
  position: fixed;
  bottom: 0; left: 0;
  width: 100%;
  height: 28px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 33%,
    var(--bm-structure-dark)   33%, var(--bm-structure-dark)   66%,
    var(--bm-structure)        66%, var(--bm-structure)        100%
  );
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
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
  bottom: 0; right: 8px;
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

/* ── Header bar (shadow style) ── */
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 44px;
  z-index: 1000;
  background: linear-gradient(
    to bottom,
    var(--bm-structure) 0%, var(--bm-structure) 85%,
    var(--bm-structure-dark) 100%
  );
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
}

.beamer-foot-bg {
  position: fixed;
  bottom: 0; left: 0;
  width: 100%;
  height: 28px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-structure-darker) 0%,  var(--bm-structure-darker) 33%,
    var(--bm-structure-dark)   33%, var(--bm-structure-dark)   66%,
    var(--bm-structure)        66%, var(--bm-structure)        100%
  );
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
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
  bottom: 0; right: 8px;
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

/* ── Header bar (infolines) ── */
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 40px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-blue)       0%,  var(--bm-blue)       33%,
    var(--bm-maize-dark) 33%, var(--bm-maize-dark)  66%,
    var(--bm-maize)      66%, var(--bm-maize)       100%
  );
}

.beamer-foot-bg {
  position: fixed;
  bottom: 0; left: 0;
  width: 100%;
  height: 28px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-blue)       0%,  var(--bm-blue)       33%,
    var(--bm-maize-dark) 33%, var(--bm-maize-dark)  66%,
    var(--bm-maize)      66%, var(--bm-maize)       100%
  );
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
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
  bottom: 0; right: 8px;
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

/* ── Sidebar (left) + top bar ── */
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100px;
  height: 100%;
  z-index: 1000;
  background: var(--bm-structure);
}

.beamer-foot-bg {
  position: fixed;
  top: 0; left: 100px;
  width: calc(100% - 100px);
  height: 36px;
  z-index: 1000;
  background: var(--bm-structure-dark);
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
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
  bottom: 0; right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-structure);
  border-radius: 0;
}
"""

    # =====================================================================
    # Stanford
    # =====================================================================
    if theme_key == "stanford":
        return r"""
/* Stanford theme – Cardinal red/white/black with striped header/footer */
:root {
  --bm-cardinal:       #8C1515;
  --bm-cardinal-dark:  #820000;
  --bm-white:          #FFFFFF;
  --bm-black:          #2E2D29;
  --bm-cool-gray:      #53565A;
  --bm-palo-alto:      #175E54;
  --bm-structure:      #8C1515;

  --bm-block-bg:         #8C1515;
  --bm-block-body-bg:    #F5E1E1;
  --bm-alert-bg:         #820000;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #175E54;
  --bm-example-body-bg:  #DEF0DE;
}

/* ── Header background bar ── */
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 40px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-cardinal)  0%,   var(--bm-cardinal)  25%,
    var(--bm-white)     25%,  var(--bm-white)     50%,
    var(--bm-black)     50%,  var(--bm-black)     75%,
    var(--bm-cool-gray) 75%,  var(--bm-cool-gray) 100%
  );
}

/* ── Footer background bar (matching stripe pattern) ── */
.beamer-foot-bg {
  position: fixed;
  bottom: 0; left: 0;
  width: 100%;
  height: 28px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-cardinal)  0%,   var(--bm-cardinal)  25%,
    var(--bm-white)     25%,  var(--bm-white)     50%,
    var(--bm-black)     50%,  var(--bm-black)     75%,
    var(--bm-cool-gray) 75%,  var(--bm-cool-gray) 100%
  );
}

/* ── Header text: left side white (over red), title black (over white) ── */
.beamer-headline {
  color: #fff;
  font-size: 22px;
}

.beamer-headline .beamer-head-title {
  color: #000;
}

/* ── Footer text aligned to stripe colors ── */
.beamer-footline {
  font-size: 14px;
}

.beamer-footline .beamer-foot-left {
  color: #fff;  /* white text over cardinal red stripe */
}

.beamer-footline .beamer-foot-center {
  color: #820000;  /* cardinal dark text over white stripe */
}

.beamer-footline .beamer-foot-right {
  color: #fff;  /* white text over black stripe */
}

.beamer-slide-number {
  color: #fff !important;
  font-size: 14px;
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-cardinal)  0%,   var(--bm-cardinal)  25%,
    var(--bm-white)     25%,  var(--bm-white)     50%,
    var(--bm-black)     50%,  var(--bm-black)     75%,
    var(--bm-cool-gray) 75%,  var(--bm-cool-gray) 100%
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
    var(--bm-cardinal)  0%,   var(--bm-cardinal)  25%,
    var(--bm-white)     25%,  var(--bm-white)     50%,
    var(--bm-black)     50%,  var(--bm-black)     75%,
    var(--bm-cool-gray) 75%,  var(--bm-cool-gray) 100%
  );
  z-index: 1000;
}

.reveal h2 {
  background: var(--bm-cardinal);
  color: #fff;
  padding: 0.2em 0.6em;
  border-radius: 6px;
  font-size: 1.15em;
  margin-bottom: 0.5em;
}

.reveal h1 {
  color: var(--bm-cardinal);
  font-size: 1.3em;
}

.reveal .slides section {
  padding-top: 56px;
  padding-bottom: 44px;
}

.reveal .slide-number {
  background: var(--bm-cardinal);
  color: #fff;
  bottom: 0; right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-cardinal);
  border-radius: 8px;
}

/* Bullet color */
.reveal {
  --beamer-bullet: #8C1515;
}
"""

    # =====================================================================
    # Gamecocks (South Carolina)
    # =====================================================================
    if theme_key == "gamecocks":
        return r"""
/* Gamecocks theme – South Carolina garnet and black */
:root {
  --bm-garnet:       #73000A;
  --bm-garnet-dark:  #5C0008;
  --bm-black:        #000000;
  --bm-white:        #FFFFFF;
  --bm-structure:    #73000A;

  --bm-block-bg:         #73000A;
  --bm-block-body-bg:    #F5E1E2;
  --bm-alert-bg:         #5C0008;
  --bm-alert-body-bg:    #F2DEDE;
  --bm-example-bg:       #006000;
  --bm-example-body-bg:  #DEF0DE;
}

/* ── Header background bar ── */
.beamer-head-bg {
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 40px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-garnet) 0%,      var(--bm-garnet) 50%,
    var(--bm-black)  50%,     var(--bm-black)  100%
  );
}

/* ── Footer background bar ── */
.beamer-foot-bg {
  position: fixed;
  bottom: 0; left: 0;
  width: 100%;
  height: 28px;
  z-index: 1000;
  background: linear-gradient(
    to right,
    var(--bm-garnet-dark) 0%,   var(--bm-garnet-dark) 33%,
    var(--bm-garnet)      33%,  var(--bm-garnet)      66%,
    var(--bm-black)       66%,  var(--bm-black)       100%
  );
}

/* ── Header text ── */
.beamer-headline {
  color: #fff;
  font-size: 22px;
}

/* ── Footer text ── */
.beamer-footline {
  font-size: 14px;
  color: #fff;
}

.beamer-slide-number {
  color: #fff !important;
  font-size: 14px;
}

/* ── Fallback: pseudo-elements for non-JS scenarios ── */
.reveal::before {
  content: "";
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 40px;
  background: linear-gradient(
    to right,
    var(--bm-garnet) 0%,      var(--bm-garnet) 50%,
    var(--bm-black)  50%,     var(--bm-black)  100%
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
    var(--bm-garnet-dark) 0%,   var(--bm-garnet-dark) 33%,
    var(--bm-garnet)      33%,  var(--bm-garnet)      66%,
    var(--bm-black)       66%,  var(--bm-black)       100%
  );
  z-index: 1000;
}

.reveal h2 {
  background: var(--bm-garnet);
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
  background: var(--bm-garnet);
  color: #fff;
  bottom: 0; right: 8px;
  z-index: 1002;
}

.beamer-title-box {
  background: var(--bm-garnet);
  border-radius: 8px;
}

/* Bullet color */
.reveal {
  --beamer-bullet: #73000A;
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
    # We set reveal_theme to 'white' (the most minimal Reveal.js theme)
    # and reveal_number to 'c/t' for "current / total" slide numbers.
    template_content = (
        '{%- extends "reveal/index.html.j2" -%}\n'
        "\n"
        "{% set reveal_theme = 'white' %}\n"
        "{% set reveal_number = 'h.v/t' %}\n"
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
        "stanford": "stanford",
        "gamecocks": "gamecocks",
        "south carolina": "gamecocks",
        "usc": "gamecocks",
    }
    if t not in aliases:
        raise ValueError(f"Unknown theme '{theme}'.")
    return aliases[t]


# =============================================================================
# Per-slide CSS helpers — read notebook metadata, compute RISE slide IDs,
# and inject targeted CSS for slides that carry specific cell tags.
# =============================================================================

def _detect_notebook_path() -> Path:
    """
    Try to auto-detect the path of the currently running notebook.

    Strategy:
    1. Try ``ipynbname`` (pip install ipynbname) — most reliable.
    2. Fall back to globbing ``*.ipynb`` in cwd; use it if exactly one match.
    3. Raise with a helpful message otherwise.
    """
    # Attempt 1: ipynbname
    try:
        import ipynbname
        return Path(ipynbname.path())
    except Exception:
        pass

    # Attempt 2: single .ipynb in cwd
    notebooks = list(Path.cwd().glob("*.ipynb"))
    # Filter out checkpoint files
    notebooks = [p for p in notebooks if ".ipynb_checkpoints" not in str(p)]
    if len(notebooks) == 1:
        return notebooks[0]
    if len(notebooks) == 0:
        raise FileNotFoundError(
            "No .ipynb files found in the current directory. "
            "Pass notebook_path= explicitly."
        )
    raise FileNotFoundError(
        f"Multiple .ipynb files in the current directory ({len(notebooks)} found). "
        "Pass notebook_path= explicitly, e.g.:\n"
        "  get_slide_info('MyPresentation.ipynb')"
    )


def get_slide_info(notebook_path=None):
    """
    Read a notebook's ``.ipynb`` JSON and return a DataFrame mapping every
    cell to its RISE slide ID, slide type, tags, and a source preview.

    Parameters
    ----------
    notebook_path : str or Path, optional
        Path to the ``.ipynb`` file.  If *None*, auto-detects the notebook
        in the current directory (see ``_detect_notebook_path``).

    Returns
    -------
    pandas.DataFrame
        Columns: ``cell_index``, ``cell_type``, ``slide_type``, ``slide_id``,
        ``tags``, ``source_preview``.
    """
    import pandas as pd

    nb_path = Path(notebook_path) if notebook_path else _detect_notebook_path()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.loads(f.read())

    rows = []
    h = -1          # horizontal slide index (0-based)
    v = 0           # vertical sub-slide index (0-based)
    current_id = ""

    for i, cell in enumerate(nb.get("cells", [])):
        meta = cell.get("metadata", {})
        slide_type = meta.get("slideshow", {}).get("slide_type", "")
        tags = meta.get("tags", [])
        if tags is None:
            tags = []
        source = "".join(cell.get("source", []))
        preview = source.replace("\n", " ")[:80]

        # Compute RISE slide ID
        if slide_type == "slide":
            h += 1
            v = 0
            current_id = f"slide-{h}-{v}"
        elif slide_type == "subslide":
            v += 1
            current_id = f"slide-{h}-{v}"
        elif slide_type == "fragment":
            # Fragments belong to the current slide — same ID
            pass
        elif slide_type in ("skip", "notes"):
            current_id = ""
        elif slide_type in ("-", ""):
            # Continuation — belongs to the current slide if one exists
            if h < 0:
                current_id = ""

        rows.append({
            "cell_index": i,
            "cell_type": cell.get("cell_type", ""),
            "slide_type": slide_type,
            "slide_id": current_id,
            "tags": tags,
            "source_preview": preview,
        })

    return pd.DataFrame(rows)


def get_slide_tags(notebook_path=None):
    """
    Return only the slides that have cell tags, with a convenience ``tag``
    column holding the first tag as a plain string.

    Parameters
    ----------
    notebook_path : str or Path, optional
        Passed through to :func:`get_slide_info`.

    Returns
    -------
    pandas.DataFrame
        Same columns as ``get_slide_info`` plus ``tag`` (first tag string).
    """
    df = get_slide_info(notebook_path)
    # Keep only rows with non-empty tags
    mask = df["tags"].apply(lambda t: len(t) > 0 if isinstance(t, list) else False)
    tagged = df[mask].copy()
    tagged["tag"] = tagged["tags"].apply(lambda t: t[0] if t else "")
    return tagged.reset_index(drop=True)


def apply_slide_css(
    tag_css: Dict[str, str],
    notebook_path=None,
    *,
    hide_input: bool = True,
):
    """
    Inject per-slide CSS targeting RISE slide IDs based on cell tags.

    Parameters
    ----------
    tag_css : dict
        Mapping of tag name → CSS declarations.  Example::

            {
                "full": "top: 0 !important; height: 90% !important; width: 95% !important;",
                "map":  "top: 0 !important; height: 70% !important; width: 90% !important;",
            }

    notebook_path : str or Path, optional
        Passed through to :func:`get_slide_tags`.

    hide_input : bool, default True
        If *True*, also hides the code-input area for tagged slides.
    """
    from IPython.display import display, HTML

    tagged = get_slide_tags(notebook_path)
    if tagged.empty:
        print("No tagged slides found — nothing to apply.")
        return

    css_parts = ["/* === Per-slide CSS from apply_slide_css() === */\n"]
    applied = []

    for _, row in tagged.iterrows():
        tag = row["tag"]
        slide_id = row["slide_id"]

        if not slide_id or tag not in tag_css:
            continue

        css_body = tag_css[tag]

        # Main slide rule
        css_parts.append(
            f".reveal .slides section.present#{slide_id} {{\n"
            f"  {css_body}\n"
            f"}}\n"
        )

        # Output wrapper gets the same sizing
        css_parts.append(
            f".reveal .slides section.present#{slide_id} > div > div.output_wrapper {{\n"
            f"  {css_body}\n"
            f"}}\n"
        )

        # Optionally hide code input
        if hide_input:
            css_parts.append(
                f".reveal .slides section.present#{slide_id} > div > div.input {{\n"
                f"  display: none !important;\n"
                f"}}\n"
            )

        applied.append({
            "slide_id": slide_id,
            "tag": tag,
            "css": css_body[:60] + ("..." if len(css_body) > 60 else ""),
        })

    if not applied:
        print("No matching tag→CSS rules to apply.")
        return

    css_text = "\n".join(css_parts)
    display(HTML(f"<style>{css_text}</style>"))

    # Print summary
    import pandas as pd
    summary = pd.DataFrame(applied)
    print(f"\n✓ Injected CSS for {len(applied)} slide(s):")
    print(summary.to_string(index=False))


def apply_cell_tags(
    notebook_path=None,
):
    """
    Process cell-level tags and inject CSS/JS to apply display changes.

    Recognised tags (set in each cell's metadata → tags list):

    **Always active** (notebook *and* slideshow):

    * ``remove_input``  — hide the code-input area of that cell.
    * ``remove_output`` — hide the output area of that cell.
    * ``side_by_side``  — display input and output side by side.
    * ``hide_prompt``   — hide the In[N]/Out[N] prompt labels.

    **Slide-only** (hidden only during RISE presentation; fully visible
    in normal notebook editing so you can still edit the cell):

    * ``slide_remove_input``  — hide input during slideshow only.
    * ``slide_remove_output`` — hide output during slideshow only.
    * ``slide_side_by_side``  — side-by-side during slideshow only.
    * ``slide_hide_prompt``   — hide In[N]/Out[N] prompts during slideshow only.

    Can be called standalone or automatically via
    ``apply_beamer_theme(..., cell_tags=True)``.

    Parameters
    ----------
    notebook_path : str or Path, optional
        The ``.ipynb`` file to read.  If omitted the notebook is
        auto-detected (single ``.ipynb`` in cwd, or via ``ipynbname``).
    """
    from IPython.display import display, HTML

    RECOGNISED_TAGS = {
        "remove_input", "remove_output", "side_by_side",
        "slide_remove_input", "slide_remove_output", "slide_side_by_side",
        "hide_prompt", "slide_hide_prompt",
    }

    df = get_slide_info(notebook_path)

    # Build a mapping: cell_index → set of recognised tags
    tag_map = {}  # {cell_index: set_of_tags}
    for _, row in df.iterrows():
        tags = row["tags"]
        if not isinstance(tags, list):
            continue
        matched = set(tags) & RECOGNISED_TAGS
        if matched:
            tag_map[int(row["cell_index"])] = matched

    if not tag_map:
        print("No cells with recognised display tags found.")
        return

    # ---- CSS rules ----
    css = """
/* === Cell-tag display rules from apply_cell_tags() === */

/* --------------------------------------------------------
   ALWAYS-ACTIVE variants (notebook + slideshow)
   -------------------------------------------------------- */

/* remove_input: hide the input/code area */
.cell.beamer-remove-input > .input,
.cell.beamer-remove-input > .jp-Cell-inputWrapper,
.cell.beamer-remove-input > .inner_cell > .input_area {
  display: none !important;
}

/* remove_output: hide the output area */
.cell.beamer-remove-output > .output_wrapper,
.cell.beamer-remove-output > .jp-Cell-outputWrapper,
.cell.beamer-remove-output > .inner_cell > .output_wrapper {
  display: none !important;
}

/* side_by_side: input and output next to each other */
.cell.beamer-side-by-side {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: flex-start !important;
}
.cell.beamer-side-by-side > .input,
.cell.beamer-side-by-side > .jp-Cell-inputWrapper {
  flex: 1 1 48% !important;
  min-width: 0 !important;
  max-width: 50% !important;
}
.cell.beamer-side-by-side > .output_wrapper,
.cell.beamer-side-by-side > .jp-Cell-outputWrapper {
  flex: 1 1 48% !important;
  min-width: 0 !important;
  max-width: 50% !important;
}

/* --------------------------------------------------------
   SLIDE-ONLY variants (only during RISE / Reveal.js)
   Scoped under .reveal .slides so normal editing is
   unaffected — you can still see and edit the cell.
   -------------------------------------------------------- */

/* slide_remove_input */
.reveal .slides .cell.beamer-slide-remove-input > .input,
.reveal .slides .cell.beamer-slide-remove-input > .jp-Cell-inputWrapper,
.reveal .slides .cell.beamer-slide-remove-input > .inner_cell > .input_area {
  display: none !important;
}

/* slide_remove_output */
.reveal .slides .cell.beamer-slide-remove-output > .output_wrapper,
.reveal .slides .cell.beamer-slide-remove-output > .jp-Cell-outputWrapper,
.reveal .slides .cell.beamer-slide-remove-output > .inner_cell > .output_wrapper {
  display: none !important;
}

/* slide_side_by_side */
.reveal .slides .cell.beamer-slide-side-by-side {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: flex-start !important;
}
.reveal .slides .cell.beamer-slide-side-by-side > .input,
.reveal .slides .cell.beamer-slide-side-by-side > .jp-Cell-inputWrapper {
  flex: 1 1 48% !important;
  min-width: 0 !important;
  max-width: 50% !important;
}
.reveal .slides .cell.beamer-slide-side-by-side > .output_wrapper,
.reveal .slides .cell.beamer-slide-side-by-side > .jp-Cell-outputWrapper {
  flex: 1 1 48% !important;
  min-width: 0 !important;
  max-width: 50% !important;
}

/* --------------------------------------------------------
   PROMPT HIDING (In[N] / Out[N] labels)
   -------------------------------------------------------- */

/* hide_prompt: hide In/Out prompts (always active) */
.cell.beamer-hide-prompt .prompt,
.cell.beamer-hide-prompt .input_prompt,
.cell.beamer-hide-prompt .output_prompt,
.cell.beamer-hide-prompt .jp-InputPrompt,
.cell.beamer-hide-prompt .jp-OutputPrompt {
  display: none !important;
}

/* slide_hide_prompt: hide In/Out prompts during slideshow only */
.reveal .slides .cell.beamer-slide-hide-prompt .prompt,
.reveal .slides .cell.beamer-slide-hide-prompt .input_prompt,
.reveal .slides .cell.beamer-slide-hide-prompt .output_prompt,
.reveal .slides .cell.beamer-slide-hide-prompt .jp-InputPrompt,
.reveal .slides .cell.beamer-slide-hide-prompt .jp-OutputPrompt {
  display: none !important;
}
"""

    # ---- JS to apply CSS classes to the correct cells ----
    import json as _json
    tag_map_json = _json.dumps(
        {str(k): sorted(v) for k, v in tag_map.items()}
    )

    js = f"""
<script>
(function() {{
  var TAG_MAP = {tag_map_json};

  var CLASS_MAP = {{
    "remove_input":        "beamer-remove-input",
    "remove_output":       "beamer-remove-output",
    "side_by_side":        "beamer-side-by-side",
    "slide_remove_input":  "beamer-slide-remove-input",
    "slide_remove_output": "beamer-slide-remove-output",
    "slide_side_by_side":  "beamer-slide-side-by-side",
    "hide_prompt":         "beamer-hide-prompt",
    "slide_hide_prompt":   "beamer-slide-hide-prompt"
  }};

  function applyTagClasses() {{
    var cells = document.querySelectorAll(
      ".notebook-container .cell, #notebook-container .cell, .reveal .slides .cell"
    );

    var seen = new Set();
    var ordered = [];
    cells.forEach(function(c) {{
      if (!seen.has(c)) {{
        seen.add(c);
        ordered.push(c);
      }}
    }});

    if (ordered.length === 0) {{
      document.querySelectorAll(".cell").forEach(function(c) {{
        if (!seen.has(c)) {{
          seen.add(c);
          ordered.push(c);
        }}
      }});
    }}

    for (var idxStr in TAG_MAP) {{
      var idx = parseInt(idxStr, 10);
      if (idx < ordered.length) {{
        var el = ordered[idx];
        var tags = TAG_MAP[idxStr];
        for (var i = 0; i < tags.length; i++) {{
          var cls = CLASS_MAP[tags[i]];
          if (cls && !el.classList.contains(cls)) {{
            el.classList.add(cls);
          }}
        }}
      }}
    }}
  }}

  applyTagClasses();
  setTimeout(applyTagClasses, 500);
  setTimeout(applyTagClasses, 2000);

  function hookReveal() {{
    if (window.Reveal) {{
      var bind = (typeof window.Reveal.on === "function")
        ? function(e, f) {{ window.Reveal.on(e, f); }}
        : (typeof window.Reveal.addEventListener === "function")
          ? function(e, f) {{ window.Reveal.addEventListener(e, f); }}
          : null;
      if (bind) {{
        bind("slidechanged", applyTagClasses);
        bind("ready", applyTagClasses);
      }}
    }}
  }}

  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", function() {{
      applyTagClasses();
      hookReveal();
    }});
  }} else {{
    hookReveal();
  }}
}})();
</script>
"""

    display(HTML(f"<style>{css}</style>{js}"))

    # Print summary
    summary_rows = []
    for idx, tags in sorted(tag_map.items()):
        slide_id = df.loc[df["cell_index"] == idx, "slide_id"].values
        sid = slide_id[0] if len(slide_id) > 0 else ""
        summary_rows.append({
            "cell_index": idx,
            "slide_id": sid,
            "tags": ", ".join(sorted(tags)),
        })

    import pandas as pd
    summary = pd.DataFrame(summary_rows)
    print(f"\n✓ Cell tag CSS applied for {len(summary_rows)} cell(s):")
    print(summary.to_string(index=False))


def style_slide(
    slide_css: Dict[str, str],
    *,
    hide_input: bool = False,
):
    """
    Inject arbitrary CSS for specific RISE slides, addressed by slide ID.

    Parameters
    ----------
    slide_css : dict
        Mapping of slide identifier → CSS declarations.  The key can be:

        * A full RISE id: ``"slide-7-1"``
        * A short ``H-V`` form: ``"7-1"``  (becomes ``slide-7-1``)
        * A dotted ``H.V`` form: ``"7.1"`` (becomes ``slide-7-1``)
        * A bare number: ``"7"``           (becomes ``slide-7-0``)

        The value is any CSS declarations to apply.  Example::

            style_slide({
                "7.1": "font-size: 0.7em !important;",
                "3":   "background: #fafafa !important;",
            })

    hide_input : bool, default False
        If *True*, also hides the code-input area for the targeted slides.
    """
    from IPython.display import display, HTML

    def _normalise_id(key: str) -> str:
        """Turn a user-friendly key into a 'slide-H-V' string."""
        key = key.strip()
        if key.startswith("slide-"):
            return key  # already canonical
        # Replace dots with dashes: "7.1" → "7-1"
        key = key.replace(".", "-")
        parts = key.split("-")
        if len(parts) == 1:
            return f"slide-{parts[0]}-0"
        return f"slide-{'-'.join(parts)}"

    css_parts = ["/* === Per-slide CSS from style_slide() === */\n"]
    applied = []

    for raw_id, css_body in slide_css.items():
        slide_id = _normalise_id(raw_id)

        # Main slide rule
        css_parts.append(
            f".reveal .slides section.present#{slide_id} {{\n"
            f"  {css_body}\n"
            f"}}\n"
        )

        # Output wrapper gets the same sizing
        css_parts.append(
            f".reveal .slides section.present#{slide_id} > div > div.output_wrapper {{\n"
            f"  {css_body}\n"
            f"}}\n"
        )

        # Optionally hide code input
        if hide_input:
            css_parts.append(
                f".reveal .slides section.present#{slide_id} > div > div.input {{\n"
                f"  display: none !important;\n"
                f"}}\n"
            )

        applied.append({
            "slide_id": slide_id,
            "css": css_body[:60] + ("..." if len(css_body) > 60 else ""),
        })

    if not applied:
        print("No slide CSS rules to apply.")
        return

    css_text = "\n".join(css_parts)
    display(HTML(f"<style>{css_text}</style>"))

    # Print summary
    import pandas as pd
    summary = pd.DataFrame(applied)
    print(f"\n✓ Injected CSS for {len(applied)} slide(s):")
    print(summary.to_string(index=False))


__all__ = [
    "apply_beamer_theme",
    "create_beamer_rise_theme",
    "ensure_latin_modern_webfonts",
    "get_slide_info",
    "get_slide_tags",
    "apply_slide_css",
    "apply_cell_tags",
    "style_slide",
]
