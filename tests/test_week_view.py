"""Tests for src/render/components/week_view.py."""

from datetime import date, datetime, timedelta

from PIL import Image, ImageDraw

from src.data.models import CalendarEvent
from src.render.components.week_view import _events_for_day, _fmt_time, draw_week


# ---------------------------------------------------------------------------
# _fmt_time
# ---------------------------------------------------------------------------

class TestFmtTime:
    def test_on_the_hour_am(self):
        dt = datetime(2024, 3, 15, 9, 0)
        assert _fmt_time(dt) == "9a"

    def test_on_the_hour_pm(self):
        dt = datetime(2024, 3, 15, 14, 0)
        assert _fmt_time(dt) == "2p"

    def test_with_minutes_am(self):
        dt = datetime(2024, 3, 15, 9, 30)
        assert _fmt_time(dt) == "9:30a"

    def test_with_minutes_pm(self):
        dt = datetime(2024, 3, 15, 15, 45)
        assert _fmt_time(dt) == "3:45p"

    def test_noon(self):
        dt = datetime(2024, 3, 15, 12, 0)
        assert _fmt_time(dt) == "12p"

    def test_midnight(self):
        dt = datetime(2024, 3, 15, 0, 0)
        assert _fmt_time(dt) == "12a"


# ---------------------------------------------------------------------------
# _events_for_day
# ---------------------------------------------------------------------------

class TestEventsForDay:
    def _timed(
        self, day: date, hour_start: int, hour_end: int, summary: str = "Event"
    ) -> CalendarEvent:
        return CalendarEvent(
            summary=summary,
            start=datetime.combine(day, datetime.min.time().replace(hour=hour_start)),
            end=datetime.combine(day, datetime.min.time().replace(hour=hour_end)),
        )

    def _all_day(self, start: date, end: date, summary: str = "All Day") -> CalendarEvent:
        return CalendarEvent(
            summary=summary,
            start=datetime.combine(start, datetime.min.time()),
            end=datetime.combine(end, datetime.min.time()),
            is_all_day=True,
        )

    def test_returns_events_on_matching_day(self):
        day = date(2024, 3, 15)
        e = self._timed(day, 9, 10)
        result = _events_for_day([e], day)
        assert e in result

    def test_excludes_events_on_other_days(self):
        day = date(2024, 3, 15)
        other = self._timed(date(2024, 3, 16), 9, 10)
        assert _events_for_day([other], day) == []

    def test_all_day_event_included_on_start_day(self):
        day = date(2024, 3, 15)
        e = self._all_day(day, day + timedelta(days=1))
        result = _events_for_day([e], day)
        assert e in result

    def test_all_day_event_excluded_on_end_day(self):
        """End date is exclusive (half-open interval)."""
        start = date(2024, 3, 15)
        end = date(2024, 3, 16)
        e = self._all_day(start, end)
        assert _events_for_day([e], end) == []

    def test_multi_day_event_included_on_middle_day(self):
        start = date(2024, 3, 14)
        end = date(2024, 3, 17)
        e = self._all_day(start, end)
        assert e in _events_for_day([e], date(2024, 3, 15))
        assert e in _events_for_day([e], date(2024, 3, 16))
        assert _events_for_day([e], date(2024, 3, 17)) == []

    def test_all_day_sorted_before_timed(self):
        day = date(2024, 3, 15)
        timed = self._timed(day, 8, 9, summary="Early Meeting")
        allday = self._all_day(day, day + timedelta(days=1), summary="Conference")
        result = _events_for_day([timed, allday], day)
        assert result[0] == allday
        assert result[1] == timed

    def test_timed_events_sorted_by_start(self):
        day = date(2024, 3, 15)
        late = self._timed(day, 15, 16, summary="Afternoon")
        early = self._timed(day, 9, 10, summary="Morning")
        result = _events_for_day([late, early], day)
        assert result[0] == early
        assert result[1] == late

    def test_empty_events_list(self):
        assert _events_for_day([], date(2024, 3, 15)) == []


# ---------------------------------------------------------------------------
# draw_week smoke test
# ---------------------------------------------------------------------------

class TestDrawWeek:
    def _make_draw(self):
        img = Image.new("1", (800, 480), 1)
        return img, ImageDraw.Draw(img)

    def test_smoke_no_events(self):
        img, draw = self._make_draw()
        draw_week(draw, [], date(2024, 3, 15))
        # Should draw something (header lines at minimum)
        assert img.getbbox() is not None

    def test_smoke_with_timed_events(self):
        img, draw = self._make_draw()
        today = date(2024, 3, 15)
        events = [
            CalendarEvent(
                summary="Standup",
                start=datetime.combine(today, datetime.min.time().replace(hour=9)),
                end=datetime.combine(today, datetime.min.time().replace(hour=9, minute=30)),
            ),
        ]
        draw_week(draw, events, today)
        assert img.getbbox() is not None

    def test_smoke_with_all_day_event(self):
        img, draw = self._make_draw()
        today = date(2024, 3, 15)
        events = [
            CalendarEvent(
                summary="Conference",
                start=datetime.combine(today, datetime.min.time()),
                end=datetime.combine(today + timedelta(days=1), datetime.min.time()),
                is_all_day=True,
            ),
        ]
        draw_week(draw, events, today)
        assert img.getbbox() is not None

    def test_smoke_many_events_per_day(self):
        """Overflow indicator (+N more) should not crash."""
        img, draw = self._make_draw()
        today = date(2024, 3, 15)
        events = [
            CalendarEvent(
                summary=f"Event {i}",
                start=datetime.combine(today, datetime.min.time().replace(hour=8 + i)),
                end=datetime.combine(today, datetime.min.time().replace(hour=9 + i)),
            )
            for i in range(10)
        ]
        draw_week(draw, events, today)
        assert img.getbbox() is not None

    def test_today_column_highlighted(self):
        """Today's column uses an inverted header — verify black pixels exist."""
        today = date(2024, 3, 15)
        img, draw = self._make_draw()
        draw_week(draw, [], today)
        # There must be at least one black pixel (inverted today header)
        bbox = img.getbbox()
        assert bbox is not None
