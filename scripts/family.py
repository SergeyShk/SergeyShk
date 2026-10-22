#!/usr/bin/env python3
"""Draw assets/family.svg: the text processing family with current versions and logos."""

import html
import json
import os
import pathlib
import re
import sys
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "family.svg"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
GITHUB_MARK = (
    "M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 "
    "0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 "
    "0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 "
    "1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 "
    "1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 "
    "1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 "
    "3.58-8 8-8Z"
)

C = {
    "bg": "#ffffff",
    "card": "#f6f8fa",
    "border": "#d0d7de",
    "text": "#1f2328",
    "muted": "#59636e",
    "link": "#0969da",
    "planned": "#8c959f",
    "arrow": "#8c959f",
    "ver_bg": "#ddf4ff",
    "ver_fg": "#0969da",
    "plan_bg": "#fff8c5",
    "plan_fg": "#9a6700",
    "rust_bg": "#fff1e5",
    "rust_fg": "#bc4c00",
    "chip": "#d0d7de",
    "chip_fg": "#59636e",
}

# row: stage index; col: 0 Russian, 1 Spanish, 2 English; span: columns; sub: stacked line within a stage.
# Released libraries take the version from PyPI (or the latest GitHub release) and the logo from docs/img.
LIBS = [
    {
        "id": "anyseg",
        "name": "anySeg",
        "planned": True,
        "rust": True,
        "row": 0,
        "col": 0,
        "span": 3,
        "langs": ["RU", "ES", "EN"],
        "desc": "Tokens and sentences with offsets and a UD document model, one package for all languages",
        "replaces": "razdel, spaCy tokenizer and ~1000 lines of splitting workarounds",
    },
    {
        "id": "rumorph",
        "name": "ruMorph",
        "repo": "ruMorph",
        "pypi": "rumorph",
        "logo": "rumorph.svg",
        "logo_h": 24,
        "rust": True,
        "row": 1,
        "col": 0,
        "desc": "Morphological analyzer: lemmas, POS and UD features",
    },
    {
        "id": "esmorph",
        "name": "esMorph",
        "planned": True,
        "row": 1,
        "col": 1,
        "desc": "Spanish morphology: lemmas, POS and UD features",
        "replaces": "simplemma, spaCy tagger",
    },
    {
        "id": "rusyntax",
        "name": "ruSyntax",
        "planned": True,
        "row": 2,
        "col": 0,
        "desc": "UD dependency parser on top of ruMorph",
        "replaces": "spaCy parser",
    },
    {
        "id": "essyntax",
        "name": "esSyntax",
        "planned": True,
        "row": 2,
        "col": 1,
        "desc": "UD dependency parser on top of esMorph",
        "replaces": "spaCy parser",
    },
    {
        "id": "anyts",
        "name": "anyTS",
        "repo": "anyTS",
        "pypi": "anyts",
        "row": 3,
        "col": 0,
        "span": 3,
        "desc": "Language-independent core of ruTS, esTS and enTS: lexical diversity, cohesion, corpus measures, stylometry",
    },
    {
        "id": "ruts",
        "name": "ruTS",
        "repo": "ruTS",
        "pypi": "ruts",
        "logo": "ruts.svg",
        "logo_h": 34,
        "row": 3,
        "sub": 1,
        "col": 0,
        "desc": "Readability, diversity, cohesion, style and verse metrics",
    },
    {
        "id": "ests",
        "name": "esTS",
        "repo": "esTS",
        "pypi": "pyests",
        "logo": "ests.svg",
        "logo_h": 24,
        "row": 3,
        "sub": 1,
        "col": 1,
        "desc": "Readability, diversity, cohesion, metre and rhyme metrics",
    },
    {
        "id": "ents",
        "name": "enTS",
        "planned": True,
        "row": 3,
        "sub": 1,
        "col": 2,
        "desc": "English text statistics on the anyTS core",
    },
    {
        "id": "mcp",
        "name": "ruTS-mcp",
        "repo": "ruTS-mcp",
        "pypi": "ruts-mcp",
        "logo": "ruts-mcp.svg",
        "logo_h": 34,
        "row": 4,
        "col": 0,
        "desc": "MCP server: ruTS statistics as tools for LLM agents",
    },
    {
        "id": "adapt",
        "name": "ruTS-adapt",
        "repo": "ruTS-adapt",
        "row": 4,
        "sub": 1,
        "col": 0,
        "desc": "Adapts Russian text to a reader's level with LangGraph and ruTS",
    },
]

STAGES = [
    ("Segmentation", "tokens and sentences"),
    ("Morphology", "lemmas, POS, features"),
    ("Syntax", "dependency trees"),
    ("Statistics", "readability, diversity, cohesion, style"),
    ("Applications", "LLM agents, text adaptation"),
]

# (from, to, column of the arrow)
FLOW = [
    ("anyseg", "rumorph", 0),
    ("anyseg", "esmorph", 1),
    ("anyseg", "anyts", 2),
    ("rumorph", "rusyntax", 0),
    ("esmorph", "essyntax", 1),
    ("rusyntax", "anyts", 0),
    ("essyntax", "anyts", 1),
    ("anyts", "ruts", 0),
    ("anyts", "ests", 1),
    ("anyts", "ents", 2),
]

W = 1000
X0 = 178
COL_W = 256
GAP = 16
CARD_H = 104
WIDE_H = 84
SUB_GAP = 14
ARROW_GAP = 30
ROW_GAP = 36
TOP = 44


def fetch(url, accept="application/json"):
    headers = {"User-Agent": "SergeyShk-family-diagram", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
        return resp.read().decode()


def version(lib):
    if lib.get("pypi"):
        return json.loads(fetch(f"https://pypi.org/pypi/{lib['pypi']}/json"))["info"]["version"]
    release = json.loads(fetch(f"https://api.github.com/repos/SergeyShk/{lib['repo']}/releases/latest"))
    return release["tag_name"].lstrip("v")


def esc(text):
    return html.escape(text, quote=True)


def text_width(text, size, weight=400):
    # rough average glyph width of system sans fonts, errs on the wide side
    return len(text) * size * (0.58 if weight >= 600 else 0.5)


def wrap(text, max_w, size):
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if cur and text_width(cand, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    return [*lines, cur]


def pill(text, right, y, bg, fg, border=None):
    w = text_width(text, 11, 600) + 14
    x = right - w
    stroke = f' stroke="{border}"' if border else ""
    svg = (
        f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="19" rx="9.5" fill="{bg}"{stroke}/>'
        f'<text x="{x + w / 2:.1f}" y="{y + 13.5}" font-size="11" font-weight="600" fill="{fg}" '
        f'text-anchor="middle">{esc(text)}</text>'
    )
    return svg, w


def embed_logo(src, x, y, h):
    view_box = re.search(r'viewBox="([^"]+)"', src).group(1)
    _, _, vw, vh = map(float, view_box.split())
    inner = re.sub(r"(?s)^.*?<svg[^>]*>|</svg>\s*$", "", src)
    inner = re.sub(r"(?s)<title>.*?</title>", "", inner)
    return f'<svg x="{x}" y="{y}" width="{h * vw / vh:.1f}" height="{h}" viewBox="{view_box}">{inner}</svg>'


def card(lib, x, y, w, h, ver, logo):
    out = []
    planned = lib.get("planned")
    if planned:
        out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{C["bg"]}" '
            f'stroke="{C["planned"]}" stroke-width="1.2" stroke-dasharray="6 4"/>'
        )
    else:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{C["card"]}" stroke="{C["border"]}"/>')
    # the project's own logo, otherwise its plain name
    if logo:
        out.append(embed_logo(logo, x + 16, y + 12, lib["logo_h"]))
    else:
        color = C["muted"] if planned else C["text"]
        out.append(
            f'<text x="{x + 16}" y="{y + 31}" font-size="19" font-weight="700" fill="{color}">{esc(lib["name"])}</text>'
        )
    # status pill on the right, chips to the left of it
    right = x + w - 14
    if planned:
        svg, pw = pill("planned", right, y + 14, C["plan_bg"], C["plan_fg"])
    else:
        svg, pw = pill(f"v{ver}", right, y + 14, C["ver_bg"], C["ver_fg"])
    out.append(svg)
    right -= pw + 6
    chips = [("Rust", C["rust_bg"], C["rust_fg"], None)] if lib.get("rust") else []
    chips += [(lang, C["bg"], C["chip_fg"], C["chip"]) for lang in reversed(lib.get("langs", []))]
    for text, bg, fg, border in chips:
        svg, cw = pill(text, right, y + 14, bg, fg, border)
        out.append(svg)
        right -= cw + 5
    lines = wrap(lib["desc"], w - 32, 12.5)
    if len(lines) > 2:
        sys.exit(f"{lib['name']}: the description takes {len(lines)} lines, at most 2 fit")
    base = y + 58 if h >= CARD_H else y + 55
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + 16}" y="{base + i * 16}" font-size="12.5" fill="{C["text"]}">{esc(line)}</text>')
    foot = y + h - 12
    if planned:
        if lib.get("replaces"):
            out.append(
                f'<text x="{x + 16}" y="{foot}" font-size="11.5" font-style="italic" fill="{C["muted"]}">'
                f"replaces {esc(lib['replaces'])}</text>"
            )
    else:
        out.append(
            f'<path transform="translate({x + 16} {foot - 10}) scale(0.75)" d="{GITHUB_MARK}" fill="{C["muted"]}"/>'
            f'<text x="{x + 32}" y="{foot}" font-size="11.5" fill="{C["link"]}">SergeyShk/{esc(lib["repo"])}</text>'
        )
    return "\n".join(out)


def layout():
    """Return {id: (x, y, w, h)}, the vertical span of each stage and the bottom edge."""
    boxes, stages, y = {}, [], TOP
    for row in range(len(STAGES)):
        members = [lib for lib in LIBS if lib["row"] == row]
        ids = {lib["id"] for lib in members}
        # stacked boxes linked by arrows need room for them
        gap = ARROW_GAP if any(src in ids and dst in ids for src, dst, _ in FLOW) else SUB_GAP
        top = y
        for sub in sorted({lib.get("sub", 0) for lib in members}):
            subs = [lib for lib in members if lib.get("sub", 0) == sub]
            h = max(WIDE_H if lib.get("span", 1) > 1 else CARD_H for lib in subs)
            for lib in subs:
                span = lib.get("span", 1)
                boxes[lib["id"]] = (X0 + lib["col"] * (COL_W + GAP), y, span * COL_W + (span - 1) * GAP, h)
            y += h + gap
        y -= gap
        stages.append((top, y))
        y += ROW_GAP
    return boxes, stages, y - ROW_GAP


def arrow(x1, y1, x2, y2, dashed):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    return (
        f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="{C["arrow"]}" stroke-width="1.5" '
        f'fill="none" marker-end="url(#ah)"{dash}/>'
    )


def render(versions, logos):
    boxes, stages, bottom = layout()
    height = bottom + 76
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
        f'font-family="{FONT}" role="img" aria-label="Text processing family: from segmentation to statistics">',
        "<title>Text processing family</title>",
        f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{C["arrow"]}"/></marker></defs>',
        f'<rect width="{W}" height="{height}" fill="{C["bg"]}"/>',
    ]
    for col, name in enumerate(["Russian", "Spanish", "English"]):
        cx = X0 + col * (COL_W + GAP) + COL_W / 2
        out.append(
            f'<text x="{cx}" y="{TOP - 14}" font-size="11.5" font-weight="600" letter-spacing="1.2" '
            f'fill="{C["muted"]}" text-anchor="middle">{name.upper()}</text>'
        )
    # stage axis
    first, last = stages[0][0], stages[-1][1]
    out.append(f'<path d="M30 {first + 10} V{last - 4}" stroke="{C["arrow"]}" stroke-width="1.5" marker-end="url(#ah)"/>')
    for (title, sub), (top, end) in zip(STAGES, stages):
        mid = (top + end) / 2
        out.append(f'<circle cx="30" cy="{mid}" r="5" fill="{C["bg"]}" stroke="{C["arrow"]}" stroke-width="2"/>')
        sub_lines = wrap(sub, 118, 11.5)
        y0 = mid - len(sub_lines) * 7 + 2
        out.append(f'<text x="46" y="{y0}" font-size="14" font-weight="700" fill="{C["text"]}">{title}</text>')
        for i, line in enumerate(sub_lines):
            out.append(f'<text x="46" y="{y0 + 17 + i * 14}" font-size="11.5" fill="{C["muted"]}">{esc(line)}</text>')
    planned = {lib["id"] for lib in LIBS if lib.get("planned")}
    for src, dst, col in FLOW:
        cx = X0 + col * (COL_W + GAP) + COL_W / 2
        out.append(arrow(cx, boxes[src][1] + boxes[src][3] + 2, cx, boxes[dst][1] - 2, src in planned or dst in planned))
    # ruTS feeds both applications through the left margin
    rx, ry, _, rh = boxes["ruts"]
    for app in ("mcp", "adapt"):
        _, ay, _, ah = boxes[app]
        out.append(
            f'<path d="M{rx - 1} {ry + rh / 2} H{rx - 9} V{ay + ah / 2} H{rx - 2}" stroke="{C["arrow"]}" '
            f'stroke-width="1.5" fill="none" marker-end="url(#ah)"/>'
        )
    for lib in LIBS:
        out.append(card(lib, *boxes[lib["id"]], versions.get(lib["id"]), logos.get(lib["id"])))
    ly = bottom + 40
    out.append(
        f'<rect x="24" y="{ly - 12}" width="26" height="16" rx="4" fill="{C["card"]}" stroke="{C["border"]}"/>'
        f'<text x="58" y="{ly}" font-size="12" fill="{C["muted"]}">released: version and repository</text>'
        f'<rect x="276" y="{ly - 12}" width="26" height="16" rx="4" fill="none" stroke="{C["planned"]}" '
        f'stroke-dasharray="4 3"/>'
        f'<text x="310" y="{ly}" font-size="12" fill="{C["muted"]}">planned: what it will replace</text>'
    )
    svg, _ = pill("Rust", 560, ly - 14, C["rust_bg"], C["rust_fg"])
    out.append(svg)
    out.append(f'<text x="568" y="{ly}" font-size="12" fill="{C["muted"]}">Rust core with Python API</text>')
    out.append("</svg>\n")
    return "\n".join(out)


def main():
    released = [lib for lib in LIBS if not lib.get("planned")]
    versions = {lib["id"]: version(lib) for lib in released}
    logos = {
        lib["id"]: fetch(f"https://raw.githubusercontent.com/SergeyShk/{lib['repo']}/HEAD/docs/img/{lib['logo']}", "*/*")
        for lib in released
        if lib.get("logo")
    }
    print(", ".join(f"{k} {v}" for k, v in versions.items()))
    OUT.write_text(render(versions, logos))


if __name__ == "__main__":
    main()
