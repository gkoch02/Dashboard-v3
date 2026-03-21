"""D&D Fantasy theme — swords & sorcery aesthetic for the eInk dashboard.

Layout: left sidebar (220px) containing the arcane tower panels stacked vertically,
with the quest log (week view) dominating the right 580px.  A thick ornamental
double-frame border and runic diamond ornaments are drawn on top of all components
via ``ThemeLayout.overlay_fn``.

Visual style:
- Cinzel (Roman inscription caps) for all headers and section labels.
- Plus Jakarta Sans for body text (events, weather details) — legible at small sizes.
- Black canvas (inverted fg/bg) with white text and ornaments.
- Thick filled header with title flanked by drawn sword glyphs.
- Sidebar panels: "THE ORACLE'S OMEN", "THE FELLOWSHIP", "ANCIENT WISDOM".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.render.fonts import cinzel_bold, cinzel_semibold, regular, medium
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle

if TYPE_CHECKING:
    from PIL import ImageDraw


# ---------------------------------------------------------------------------
# Layout geometry
# ---------------------------------------------------------------------------

_CANVAS_W = 800
_CANVAS_H = 480

_HEADER_H = 50          # tall masthead for the fantasy title
_SIDEBAR_W = 215        # arcane tower on the left

_BODY_Y = _HEADER_H
_BODY_H = _CANVAS_H - _HEADER_H   # 430px

_QUEST_X = _SIDEBAR_W
_QUEST_W = _CANVAS_W - _SIDEBAR_W  # 585px

# Sidebar panels stacked vertically; heights must sum to _BODY_H
_WEATHER_H = 180        # oracle's omen — weather
_BIRTHDAY_H = 130       # the fellowship — birthdays
_INFO_H = _BODY_H - _WEATHER_H - _BIRTHDAY_H  # ancient wisdom — quote


# ---------------------------------------------------------------------------
# Ornamental drawing helpers
# ---------------------------------------------------------------------------

def _diamond(draw: "ImageDraw.ImageDraw", cx: int, cy: int, r: int, fill: int) -> None:
    """Draw a solid diamond (rotated square) ornament."""
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def _double_hline(
    draw: "ImageDraw.ImageDraw", y: int, x0: int, x1: int, gap: int, fill: int,
) -> None:
    """Draw a double horizontal rule (two parallel lines separated by *gap* px)."""
    draw.line([(x0, y), (x1, y)], fill=fill, width=1)
    draw.line([(x0, y + gap), (x1, y + gap)], fill=fill, width=1)


def _double_vline(
    draw: "ImageDraw.ImageDraw", x: int, y0: int, y1: int, gap: int, fill: int,
) -> None:
    """Draw a double vertical rule (two parallel lines separated by *gap* px)."""
    draw.line([(x, y0), (x, y1)], fill=fill, width=1)
    draw.line([(x + gap, y0), (x + gap, y1)], fill=fill, width=1)


def _corner_ornament(
    draw: "ImageDraw.ImageDraw", cx: int, cy: int, fill: int,
) -> None:
    """Draw a corner ornament: concentric diamond + inner dot."""
    _diamond(draw, cx, cy, 7, fill)
    _diamond(draw, cx, cy, 3, 1 - fill)   # inner diamond in opposite color


def _sword_glyph(
    draw: "ImageDraw.ImageDraw", tip_x: int, mid_y: int, length: int, fill: int,
) -> None:
    """Draw a simple sword pointing right, centred vertically at *mid_y*.

    The sword blade runs from *tip_x* leftward *length* pixels.  This gives a
    symmetric pair when mirrored for the header: ⚔ style without needing a glyph.
    """
    blade_end_x = tip_x - length
    guard_x = blade_end_x + length // 3

    # Blade (horizontal line, 2px thick)
    draw.line([(tip_x, mid_y), (blade_end_x, mid_y)], fill=fill, width=2)

    # Point: small triangle at tip
    draw.polygon([
        (tip_x, mid_y),
        (tip_x - 4, mid_y - 2),
        (tip_x - 4, mid_y + 2),
    ], fill=fill)

    # Crossguard (vertical, through guard_x)
    draw.line([(guard_x, mid_y - 8), (guard_x, mid_y + 8)], fill=fill, width=2)

    # Grip (thicker segment from guard to pommel)
    grip_end_x = blade_end_x
    draw.line([(guard_x, mid_y), (grip_end_x, mid_y)], fill=fill, width=3)

    # Pommel (small diamond)
    _diamond(draw, grip_end_x, mid_y, 4, fill)


def _draw_fantasy_overlay(
    draw: "ImageDraw.ImageDraw",
    layout: ThemeLayout,
    style: ThemeStyle,
) -> None:
    """Overlay function: draws all D&D ornamental elements on top of components."""
    W = layout.canvas_w
    H = layout.canvas_h
    fg = style.fg   # WHITE (1) on dark canvas
    bg = style.bg   # BLACK (0)

    # ------------------------------------------------------------------
    # 1. Outer double-frame border
    # ------------------------------------------------------------------
    OUTER = 2   # outer border inset from canvas edge
    INNER = 6   # inner accent line inset

    draw.rectangle([OUTER, OUTER, W - OUTER - 1, H - OUTER - 1], outline=fg, width=2)
    draw.rectangle([INNER, INNER, W - INNER - 1, H - INNER - 1], outline=fg, width=1)

    # ------------------------------------------------------------------
    # 2. Corner ornaments (at inner-frame corners)
    # ------------------------------------------------------------------
    for cx, cy in [(INNER, INNER), (W - INNER - 1, INNER),
                   (INNER, H - INNER - 1), (W - INNER - 1, H - INNER - 1)]:
        _corner_ornament(draw, cx, cy, fg)

    # ------------------------------------------------------------------
    # 3. Header bottom border — double rule with centre ornament
    # ------------------------------------------------------------------
    hdr_bottom = _HEADER_H - 1
    # Erase the default single line; replace with a decorative thick rule
    draw.rectangle([INNER + 1, hdr_bottom - 2, W - INNER - 2, hdr_bottom + 3], fill=bg)
    draw.line([(INNER + 1, hdr_bottom - 1), (W - INNER - 2, hdr_bottom - 1)],
              fill=fg, width=1)
    draw.line([(INNER + 1, hdr_bottom + 2), (W - INNER - 2, hdr_bottom + 2)],
              fill=fg, width=1)
    mid_x = W // 2
    _diamond(draw, mid_x, hdr_bottom, 5, fg)

    # ------------------------------------------------------------------
    # 4. Swords in the header flanking the title
    # ------------------------------------------------------------------
    mid_y = _HEADER_H // 2
    # Left sword (pointing right, tip toward centre)
    sword_len = 28
    left_tip_x = 35
    _sword_glyph(draw, left_tip_x + sword_len, mid_y, sword_len, fg)

    # Right sword (mirror: pointing left, tip toward centre)
    right_tip_x = W - 35 - sword_len
    # Draw the mirrored sword: blade goes from right_tip_x to the right
    blade_start = right_tip_x
    guard_x_r = blade_start + sword_len // 3 * 2
    draw.line([(blade_start, mid_y), (blade_start + sword_len, mid_y)], fill=fg, width=2)
    draw.polygon([
        (blade_start, mid_y),
        (blade_start + 4, mid_y - 2),
        (blade_start + 4, mid_y + 2),
    ], fill=fg)
    draw.line([(guard_x_r, mid_y - 8), (guard_x_r, mid_y + 8)], fill=fg, width=2)
    draw.line([(guard_x_r, mid_y), (blade_start + sword_len, mid_y)], fill=fg, width=3)
    _diamond(draw, blade_start + sword_len, mid_y, 4, fg)

    # ------------------------------------------------------------------
    # 5. Vertical divider between sidebar and quest log
    # ------------------------------------------------------------------
    div_x = _SIDEBAR_W
    # Draw a triple-line divider: thick | thin | thin
    draw.line([(div_x, _HEADER_H), (div_x, H - INNER - 1)], fill=fg, width=2)
    draw.line([(div_x + 4, _HEADER_H + 8), (div_x + 4, H - INNER - 9)], fill=fg, width=1)

    # Diamond ornaments along the divider at 1/3, 1/2, 2/3 of body height
    for frac in (0.33, 0.5, 0.67):
        oy = int(_HEADER_H + _BODY_H * frac)
        # Small gap in the thin inner line around each ornament
        draw.line([(div_x + 4, oy - 6), (div_x + 4, oy + 6)], fill=bg, width=1)
        _diamond(draw, div_x + 2, oy, 5, fg)

    # ------------------------------------------------------------------
    # 6. Horizontal dividers within the sidebar
    # ------------------------------------------------------------------
    weather_bottom = _BODY_Y + _WEATHER_H
    birthday_bottom = weather_bottom + _BIRTHDAY_H

    for rule_y in (weather_bottom, birthday_bottom):
        # Double horizontal rule spanning sidebar width (minus frame inset)
        x_lo = INNER + 1
        x_hi = _SIDEBAR_W - 1
        draw.rectangle([x_lo, rule_y - 1, x_hi, rule_y + 3], fill=bg)
        draw.line([(x_lo, rule_y), (x_hi, rule_y)], fill=fg, width=1)
        draw.line([(x_lo, rule_y + 2), (x_hi, rule_y + 2)], fill=fg, width=1)
        # Diamond at centre
        csx = (x_lo + x_hi) // 2
        _diamond(draw, csx, rule_y + 1, 4, fg)

    # ------------------------------------------------------------------
    # 7. Small diamond tick-marks along canvas mid-edges for flair
    # ------------------------------------------------------------------
    # Top and bottom edge midpoints
    for mx, my in [(W // 2, INNER), (W // 2, H - INNER - 1),
                   (INNER, H // 2), (W - INNER - 1, H // 2)]:
        _diamond(draw, mx, my, 4, fg)


# ---------------------------------------------------------------------------
# Theme factory
# ---------------------------------------------------------------------------

def dnd_fantasy_theme() -> Theme:
    """Return the D&D Fantasy theme — dark canvas, Cinzel headers, ornamental borders."""

    layout = ThemeLayout(
        canvas_w=_CANVAS_W,
        canvas_h=_CANVAS_H,
        header=ComponentRegion(0, 0, _CANVAS_W, _HEADER_H),
        # Week view fills the right 585px × full body height — the "quest log"
        week_view=ComponentRegion(_QUEST_X, _BODY_Y, _QUEST_W, _BODY_H),
        # Sidebar panels stacked on the left (the "arcane tower")
        weather=ComponentRegion(0, _BODY_Y, _SIDEBAR_W, _WEATHER_H),
        birthdays=ComponentRegion(0, _BODY_Y + _WEATHER_H, _SIDEBAR_W, _BIRTHDAY_H),
        info=ComponentRegion(0, _BODY_Y + _WEATHER_H + _BIRTHDAY_H, _SIDEBAR_W, _INFO_H),
        today_view=ComponentRegion(0, 0, 0, 0, visible=False),
        draw_order=["header", "weather", "birthdays", "info", "week_view"],
        overlay_fn=_draw_fantasy_overlay,
    )

    style = ThemeStyle(
        fg=1,                           # WHITE on black canvas
        bg=0,                           # BLACK background
        invert_header=True,             # filled black header bar (already black = canvas bg)
        invert_today_col=True,          # white-filled today column with black text
        invert_allday_bars=True,        # solid white bars for all-day events
        spacing_scale=0.9,              # slightly compact — more quests visible
        label_font_size=10,
        label_font_weight="bold",
        # Cinzel for labels/headers; Plus Jakarta Sans for body (readable at small sizes)
        font_regular=regular,
        font_medium=medium,
        font_semibold=cinzel_semibold,  # event titles in Cinzel semibold
        font_bold=cinzel_bold,          # headers and day numbers in Cinzel bold
        component_labels={
            "weather": "THE ORACLE'S OMEN",
            "birthdays": "THE FELLOWSHIP",
            "info": "ANCIENT WISDOM",
        },
    )

    return Theme(name="dnd_fantasy", style=style, layout=layout)
