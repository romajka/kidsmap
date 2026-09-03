#!/usr/bin/env python
"""Regenerate the admin SVG icon sprite (place form and places changelist).

The admin used to render icons as Material Symbols ligatures
(``<span class="ms">save</span>``). That cannot work with the font shipped in
``static/fonts/``: this build carries no ligature table at all (no ``liga``
feature, zero ligature substitutions), so the browser rendered the literal
word "save". Instead of depending on a font at all, we extract the very same
glyph outlines once and inline them as an SVG sprite — an icon can then never
degrade into text.

Usage:
    python scripts/build_place_form_icons.py
"""

from __future__ import annotations

from pathlib import Path

from fontTools.misc.transform import Identity
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "static" / "fonts" / "MaterialSymbolsRounded.woff2"
TARGET = ROOT / "src" / "catalog" / "templates" / "admin" / "catalog" / "includes" / "km_icon_sprite.html"

ICONS = [
    "account_circle", "add", "add_photo_alternate", "arrow_back", "arrow_downward", "arrow_forward",
    "assessment", "auto_awesome", "block", "campaign", "chat_bubble", "check",
    "check_circle", "chevron_left", "chevron_right", "close", "cloud_done", "content_copy",
    "delete", "drag_indicator", "edit", "edit_note", "error", "expand_less",
    "expand_more", "fact_check", "file_download", "filter_alt", "history_edu", "home",
    "hourglass_empty", "hourglass_top", "image", "imagesmode", "info", "insights",
    "language", "lightbulb", "link_off", "location_off", "location_on", "map",
    "menu", "more_horiz", "my_location", "open_in_new", "payments", "pending",
    "person", "person_outline", "photo_camera", "photo_library", "place", "progress_activity",
    "public", "radio_button_checked", "radio_button_unchecked", "remove", "restore_from_trash", "save",
    "search", "search_off", "sell", "star", "tune", "unfold_more",
    "upload", "upload_file", "verified_user", "view_column", "visibility", "visibility_off",
    "warning",
]

# Names this build of Material Symbols spells differently.
ALIAS = {
    "location_on": "place",
    "assessment": "bar_chart",
    "file_download": "download",
    "person_outline": "person_2",
}

HEADER = """{% comment %}
  Admin icon sprite — GENERATED FILE, do not edit by hand.

  Built from static/fonts/MaterialSymbolsRounded.woff2 by extracting the glyph
  outlines, because that build of the font carries no ligature table: writing
  <span class="ms">save</span> rendered the literal word instead of an icon.
  Inline SVG cannot degrade into text and needs no font to load.

  To add an icon: add its name to ICONS in scripts/build_place_form_icons.py
  and re-run that script.
{% endcomment %}
"""


def build() -> str:
    font = TTFont(FONT)
    glyphs = font.getGlyphSet()
    box = font["head"].unitsPerEm  # 960 — the Material Symbols design grid

    rows = []
    missing = []
    for name in ICONS:
        source = ALIAS.get(name, name)
        if source not in glyphs:
            missing.append(name)
            continue
        pen = SVGPathPen(glyphs)
        # Font space is y-up with the icon box at 0..960; SVG is y-down.
        glyphs[source].draw(TransformPen(pen, Identity.translate(0, box).scale(1, -1)))
        path = pen.getCommands()
        if not path:
            raise SystemExit(f"glyph has no outline: {name}")
        rows.append(f'  <symbol id="kmi-{name}" viewBox="0 0 {box} {box}"><path d="{path}"/></symbol>')

    if missing:
        raise SystemExit("glyphs missing from the font: " + ", ".join(missing))

    return (
        HEADER
        + '<svg xmlns="http://www.w3.org/2000/svg" class="km-icon-sprite" aria-hidden="true" focusable="false" hidden>\n'
        + "\n".join(rows)
        + "\n</svg>\n"
    )


if __name__ == "__main__":
    TARGET.write_text(build(), encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)} — {len(ICONS)} icons")
