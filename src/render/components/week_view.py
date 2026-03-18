from datetime import datetime, date, timedelta
from PIL import ImageDraw

from src.data.models import CalendarEvent, DayForecast
from src.render import layout as L
from src.render.fonts import (
    semibold, regular, bold, medium, fraunces_bold,
)
from src.render.icons import draw_weather_icon
from src.render.primitives import (
    BLACK, WHITE, hline, vline, dashed_vline, filled_rect,
    draw_text_truncated, draw_text_wrapped, text_height, text_width,
)

PAD = L.PAD_SM + 1  # 5px inner padding for columns

# Default maximum number of busy-ness dots shown in a day header
_DEFAULT_MAX_DOTS = 5
_DOT_SIZE = 3
_DOT_GAP = 2


def _density_tier(event_count: int, is_weekend: bool) -> str:
    """Select density tier based on event count and column type.

    Returns ``"normal"``, ``"compact"``, or ``"dense"``.
    Weekend columns have lower thresholds due to reduced height.
    """
    if is_weekend:
        if event_count >= 5:
            return "dense"
        if event_count >= 3:
            return "compact"
        return "normal"
    # Weekday
    if event_count >= 8:
        return "dense"
    if event_count >= 5:
        return "compact"
    return "normal"


def _fonts_for_tier(tier: str) -> tuple:
    """Return rendering parameters for the given density tier.

    Returns ``(time_font, title_font, allday_font, event_spacing,
    max_title_lines, show_location, allday_pad)``.
    """
    if tier == "dense":
        return (
            regular(9), medium(11),
            semibold(11),
            2, 1, False, 4,
        )
    if tier == "compact":
        return (
            regular(10), medium(12),
            semibold(11),
            3, 1, False, 4,
        )
    # normal
    return (
        regular(11), semibold(14),
        semibold(13),
        6, 2, True, 6,
    )


def _fmt_time(dt: datetime) -> str:
    """Format a datetime as a compact am/pm string, e.g. '9:30a', '2p'."""
    s = dt.strftime("%-I:%M%p").lower().replace(":00", "")
    return s.replace("am", "a").replace("pm", "p")


def draw_week(
    draw: ImageDraw.ImageDraw,
    events: list[CalendarEvent],
    today: date,
    forecast: list[DayForecast] | None = None,
    max_busy_dots: int = _DEFAULT_MAX_DOTS,
):
    """Draw the 7-day calendar grid starting from the Monday of the current week.

    When *forecast* is provided, small weather icons are drawn in column headers
    for days that have forecast data, giving a unified week-at-a-glance view.

    *max_busy_dots* controls the cap on busy-ness dots per column header.
    """
    # Find Monday of this week (weekday() == 0 for Monday)
    week_start = today - timedelta(days=today.weekday())

    # Index forecast by date for O(1) lookup per column
    forecast_by_date: dict[date, DayForecast] = {}
    if forecast:
        for fc in forecast:
            forecast_by_date[fc.date] = fc

    header_h = L.WEEK_HEADER_H
    x0 = L.WEEK_X
    y0 = L.WEEK_Y
    body_top = y0 + header_h
    body_h = L.WEEK_H - header_h

    day_label_font = semibold(11)
    day_num_font = bold(16)

    date_section_h = L.WEEK_DATE_SECTION_H
    date_section_font = fraunces_bold(100)
    date_y = body_top + body_h - date_section_h  # top of combined date cell

    # Saturday is col 5 (Mon=0 … Sat=5, Sun=6)
    SAT_COL = 5
    sat_cx = x0 + SAT_COL * L.WEEK_COL_W
    combined_date_w = L.WEEK_COL_W + L.WEEK_LAST_COL_W  # 114 + 116 = 230px

    week_end = week_start + timedelta(days=7)

    # --- Multi-day spanning event bars (rendered above per-day content) ---
    spanning = _collect_spanning_events(events, week_start, week_end)
    spanning_ids: set[str | None] = set()  # track which events are rendered as spanning
    allday_font = semibold(13)
    span_bar_h = text_height(allday_font) + 6
    span_spacing = 2
    span_total_h = 0
    if spanning:
        for evt, first_col, last_col in spanning:
            # Mark event so it's excluded from per-day single-col rendering
            spanning_ids.add(id(evt))

            bar_y = body_top + PAD + span_total_h
            bar_x0 = x0 + first_col * L.WEEK_COL_W + PAD - 1
            last_col_w = L.WEEK_LAST_COL_W if last_col == L.WEEK_COL_COUNT - 1 else L.WEEK_COL_W
            bar_x1 = x0 + last_col * L.WEEK_COL_W + last_col_w - PAD

            filled_rect(draw, (bar_x0, bar_y, bar_x1, bar_y + span_bar_h), fill=BLACK)
            bar_text_w = bar_x1 - bar_x0 - PAD * 2
            draw_text_truncated(
                draw, (bar_x0 + PAD, bar_y + 3),
                evt.summary, allday_font, bar_text_w, fill=WHITE,
            )
            span_total_h += span_bar_h + span_spacing

    for col in range(L.WEEK_COL_COUNT):
        day = week_start + timedelta(days=col)
        col_w = L.WEEK_LAST_COL_W if col == L.WEEK_COL_COUNT - 1 else L.WEEK_COL_W
        cx = x0 + col * L.WEEK_COL_W
        is_today = day == today

        # Pre-compute events for this day — used for both busy dots and event drawing
        day_events = _events_for_day(events, day)

        # Column header
        day_abbr = day.strftime("%a").upper()
        day_num = str(day.day)
        header_text = f"{day_abbr} {day_num}"

        is_weekend = day.weekday() >= 5  # Sat=5, Sun=6

        if is_today:
            # Inverted header for today
            filled_rect(draw, (cx, y0, cx + col_w - 1, y0 + header_h - 1), fill=BLACK)
            fnt = bold(16)
            th = text_height(fnt)
            ty = y0 + (header_h - th) // 2
            draw.text((cx + PAD, ty), header_text, font=fnt, fill=WHITE)
        elif is_weekend:
            # Weekend: lighter styling — regular weight instead of semibold
            wknd_abbr_font = regular(11)
            wknd_num_font = regular(16)
            th = text_height(wknd_num_font)
            ty = y0 + (header_h - th) // 2
            draw.text((cx + PAD, ty), day_abbr, font=wknd_abbr_font, fill=BLACK)
            abbr_w = text_width(draw, day_abbr + " ", wknd_abbr_font)
            draw.text((cx + PAD + abbr_w, ty), day_num, font=wknd_num_font, fill=BLACK)
        else:
            th = text_height(day_label_font)
            ty = y0 + (header_h - th) // 2
            draw.text((cx + PAD, ty), day_abbr, font=day_label_font, fill=BLACK)
            abbr_w = text_width(draw, day_abbr + " ", day_label_font)
            draw.text((cx + PAD + abbr_w, ty), day_num, font=day_num_font, fill=BLACK)

        # Small forecast icon in column header (between day label and busy dots)
        fc = forecast_by_date.get(day)
        if fc:
            _FORECAST_ICON_SIZE = 12
            # Position: right of header text, vertically centred in header
            icon_x = (
                cx + col_w - PAD
                - (max_busy_dots * (_DOT_SIZE + _DOT_GAP))
                - _FORECAST_ICON_SIZE - 4
            )
            icon_y = y0 + (header_h - _FORECAST_ICON_SIZE) // 2
            icon_fill = WHITE if is_today else BLACK
            draw_weather_icon(
                draw, (icon_x, icon_y), fc.icon,
                size=_FORECAST_ICON_SIZE, fill=icon_fill,
            )

        # Busy-ness dots: one filled square per event (capped at max_busy_dots), right-aligned
        _draw_busy_dots(draw, len(day_events), cx, y0, col_w, header_h, is_today, max_busy_dots)

        # Header underline
        hline(draw, y0 + header_h - 1, cx, cx + col_w - 1)

        # Column separator (right edge).
        # Between Sat and Sun, stop above the merged date cell.
        # Friday's right edge (= Saturday's left edge) also stops at the date
        # cell so we can draw a solid border around the combined date section.
        # Solid through the header band; dashed in the event body for a lighter grid.
        FRI_COL = SAT_COL - 1
        if col < L.WEEK_COL_COUNT - 1:
            sep_bottom = (date_y - 1) if col in (FRI_COL, SAT_COL) else (y0 + L.WEEK_H - 1)
            vline(draw, cx + col_w - 1, y0, y0 + header_h - 1)
            dashed_vline(draw, cx + col_w - 1, body_top, sep_bottom)

        # Events — weekend columns give up their bottom 25% to the shared date cell.
        # Offset below any spanning bars that were drawn across the top.
        events_body_h = (body_h - date_section_h) if is_weekend else body_h
        events_y_start = body_top + span_total_h
        adjusted_body_h = events_body_h - span_total_h

        # Exclude multi-day spanning events (already drawn as continuous bars)
        day_events_filtered = [e for e in day_events if id(e) not in spanning_ids]

        if day_events_filtered:
            tier = _density_tier(len(day_events_filtered), is_weekend)
            (t_font, ti_font, ad_font,
             spacing, max_lines, show_loc, ad_pad) = _fonts_for_tier(tier)
            _draw_day_events(
                draw, day_events_filtered, cx, events_y_start,
                col_w, adjusted_body_h, t_font, ti_font,
                allday_font=ad_font, event_spacing=spacing,
                max_title_lines=max_lines, show_location=show_loc,
                allday_pad=ad_pad,
            )
        elif not day_events:  # only show dash if truly empty (no spanning events either)
            # Subtle empty indicator centred in the column
            empty_font = regular(12)
            dash = "–"
            dw = text_width(draw, dash, empty_font)
            dh = text_height(empty_font)
            draw.text(
                (cx + (col_w - dw) // 2, events_y_start + adjusted_body_h // 3 - dh // 2),
                dash, font=empty_font, fill=BLACK,
            )

    # Solid left border for the combined date cell (Saturday's left edge)
    vline(draw, sat_cx, date_y, y0 + L.WEEK_H - 1)

    # Combined "Today" cell — inverted month header, normal day number
    month_font = fraunces_bold(33)
    month_text = today.strftime("%B").upper()
    mbb = draw.textbbox((0, 0), month_text, font=month_font)
    month_w = mbb[2] - mbb[0]
    month_h = mbb[3] - mbb[1]
    month_band_h = month_h + PAD * 2

    # Black band for month header
    filled_rect(
        draw,
        (sat_cx, date_y, sat_cx + combined_date_w - 1, date_y + month_band_h - 1),
        fill=BLACK,
    )
    month_x = sat_cx + (combined_date_w - month_w) // 2 - mbb[0]
    month_y = date_y + (month_band_h - month_h) // 2 - mbb[1]
    draw.text((month_x, month_y), month_text, font=month_font, fill=WHITE)

    # Day number — black on white, centered in the remaining space below the band
    day_area_y = date_y + month_band_h
    day_area_h = date_section_h - month_band_h
    dn_text = str(today.day)
    dbb = draw.textbbox((0, 0), dn_text, font=date_section_font)
    dn_w = dbb[2] - dbb[0]
    dn_h = dbb[3] - dbb[1]
    dn_x = sat_cx + (combined_date_w - dn_w) // 2 - dbb[0]
    dn_y = day_area_y + (day_area_h - dn_h) // 2 - dbb[1]
    draw.text((dn_x, dn_y), dn_text, font=date_section_font, fill=BLACK)


def _draw_busy_dots(
    draw: ImageDraw.ImageDraw,
    event_count: int,
    cx: int,
    y0: int,
    col_w: int,
    header_h: int,
    is_today: bool,
    max_dots: int = _DEFAULT_MAX_DOTS,
) -> None:
    """Draw filled 3×3 squares right-aligned in the header to indicate how busy a day is.

    One dot per event, capped at max_dots.  Color is inverted for the today column.
    """
    if event_count == 0:
        return

    n_dots = min(event_count, max_dots)
    total_w = n_dots * _DOT_SIZE + (n_dots - 1) * _DOT_GAP
    dot_x = cx + col_w - PAD - total_w
    dot_y = y0 + (header_h - _DOT_SIZE) // 2
    dot_fill = WHITE if is_today else BLACK

    for i in range(n_dots):
        dx = dot_x + i * (_DOT_SIZE + _DOT_GAP)
        filled_rect(draw, (dx, dot_y, dx + _DOT_SIZE - 1, dot_y + _DOT_SIZE - 1), fill=dot_fill)


def _event_date_range(e: CalendarEvent) -> tuple[date, date]:
    """Return (start_date, end_date) for an event (end is exclusive)."""
    start_d = e.start.date() if isinstance(e.start, datetime) else e.start
    end_d = e.end.date() if isinstance(e.end, datetime) else e.end
    return start_d, end_d


def _is_multiday(e: CalendarEvent) -> bool:
    """Return True if the event is all-day and spans 2+ calendar days."""
    if not e.is_all_day:
        return False
    start_d, end_d = _event_date_range(e)
    return (end_d - start_d).days >= 2


def _collect_spanning_events(
    events: list[CalendarEvent], week_start: date, week_end: date,
) -> list[tuple[CalendarEvent, int, int]]:
    """Identify multi-day all-day events visible in the week and return their column spans.

    Returns a list of (event, first_col, last_col_inclusive) tuples, sorted by
    start date then summary.  Columns are 0-indexed (Mon=0, Sun=6).
    """
    result: list[tuple[CalendarEvent, int, int]] = []
    for e in events:
        if not _is_multiday(e):
            continue
        start_d, end_d = _event_date_range(e)
        # Clamp to visible week
        vis_start = max(start_d, week_start)
        vis_end = min(end_d, week_end)  # end_d is exclusive
        if vis_start >= vis_end:
            continue
        first_col = (vis_start - week_start).days
        last_col = (vis_end - week_start).days - 1  # inclusive
        result.append((e, first_col, last_col))
    result.sort(key=lambda t: (t[1], t[0].summary))
    return result


def _events_for_day(events: list[CalendarEvent], day: date) -> list[CalendarEvent]:
    """Filter events that fall on the given day."""
    result = []
    for e in events:
        if e.is_all_day:
            event_date = e.start.date() if isinstance(e.start, datetime) else e.start
            end_date = e.end.date() if isinstance(e.end, datetime) else e.end
            if event_date <= day < end_date:
                result.append(e)
        else:
            if e.start.date() == day:
                result.append(e)
    # Sort: all-day first, then by start time
    result.sort(key=lambda e: (not e.is_all_day, e.start))
    return result


def _draw_day_events(
    draw: ImageDraw.ImageDraw,
    events: list[CalendarEvent],
    cx: int,
    y_start: int,
    col_w: int,
    max_h: int,
    time_font,
    title_font,
    allday_font=None,
    event_spacing: int = 6,
    max_title_lines: int = 2,
    show_location: bool = True,
    allday_pad: int = 6,
):
    if allday_font is None:
        allday_font = semibold(13)

    y = y_start + PAD + 1
    max_w = col_w - PAD * 2 - 1
    time_h = text_height(time_font)
    title_h = text_height(title_font)
    loc_font = regular(10)
    loc_h = text_height(loc_font)

    for idx, event in enumerate(events):
        if y - y_start + title_h > max_h - PAD:
            # Draw overflow indicator with remaining count
            remaining = len(events) - idx
            draw.text((cx + PAD, y), f"+{remaining} more", font=time_font, fill=BLACK)
            break

        if event.is_all_day:
            # All-day: filled bar with white text
            bar_h = text_height(allday_font) + allday_pad
            filled_rect(draw, (cx + PAD - 1, y, cx + col_w - PAD, y + bar_h), fill=BLACK)
            draw_text_truncated(
                draw, (cx + PAD + 2, y + allday_pad // 2),
                event.summary, allday_font, max_w - 6, fill=WHITE,
            )
            y += bar_h + event_spacing
        else:
            # Timed event: "9–9:30a" style time range, title below, optional location
            start_s = _fmt_time(event.start)
            end_s = _fmt_time(event.end)
            # Only show end if it differs and fits; drop shared am/pm from start
            if event.start.strftime("%p") == event.end.strftime("%p"):
                start_s = start_s.rstrip("ap")
            time_str = f"{start_s}–{end_s}"
            draw_text_truncated(draw, (cx + PAD, y), time_str, time_font, max_w, fill=BLACK)
            y += time_h + 1
            used_h = draw_text_wrapped(
                draw, (cx + PAD, y), event.summary, title_font,
                max_w, max_lines=max_title_lines, line_spacing=1, fill=BLACK,
            )
            y += max(used_h, title_h)

            # Location line — only in normal density when there's room
            if show_location and event.location:
                loc_text = event.location.split(",")[0].strip()
                if loc_text and y - y_start + loc_h <= max_h - PAD:
                    y += 1
                    draw_text_truncated(
                        draw, (cx + PAD, y), loc_text, loc_font, max_w, fill=BLACK,
                    )
                    y += loc_h

            y += event_spacing
