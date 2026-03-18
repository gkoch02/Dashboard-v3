"""Tests for circuit breaker (src/fetchers/circuit_breaker.py)."""

from pathlib import Path

import pytest

from src.fetchers.circuit_breaker import CircuitBreaker


@pytest.fixture
def tmp_state_dir(tmp_path):
    return str(tmp_path)


class TestCircuitBreaker:
    def test_initial_state_allows_attempt(self, tmp_state_dir):
        cb = CircuitBreaker(state_dir=tmp_state_dir)
        assert cb.should_attempt("weather") is True

    def test_single_failure_stays_closed(self, tmp_state_dir):
        cb = CircuitBreaker(max_failures=3, state_dir=tmp_state_dir)
        cb.record_failure("weather")
        assert cb.should_attempt("weather") is True

    def test_opens_after_max_failures(self, tmp_state_dir):
        cb = CircuitBreaker(max_failures=3, state_dir=tmp_state_dir)
        cb.record_failure("weather")
        cb.record_failure("weather")
        cb.record_failure("weather")
        assert cb.should_attempt("weather") is False

    def test_success_resets_breaker(self, tmp_state_dir):
        cb = CircuitBreaker(max_failures=2, state_dir=tmp_state_dir)
        cb.record_failure("weather")
        cb.record_failure("weather")
        assert cb.should_attempt("weather") is False
        # Force half-open by setting cooldown to 0
        cb._cooldown_minutes = 0
        assert cb.should_attempt("weather") is True  # half_open
        cb.record_success("weather")
        assert cb.should_attempt("weather") is True  # closed

    def test_half_open_failure_reopens(self, tmp_state_dir):
        cb = CircuitBreaker(max_failures=2, cooldown_minutes=0, state_dir=tmp_state_dir)
        cb.record_failure("events")
        cb.record_failure("events")
        assert cb.should_attempt("events") is True  # cooldown=0 → half_open
        cb.record_failure("events")  # probe failed
        # Manually check: should be open again but cooldown=0 so half_open
        assert cb._states["events"].state == "open"

    def test_state_persistence(self, tmp_state_dir):
        cb1 = CircuitBreaker(max_failures=2, state_dir=tmp_state_dir)
        cb1.record_failure("weather")
        cb1.record_failure("weather")
        # Open state persisted
        cb2 = CircuitBreaker(max_failures=2, state_dir=tmp_state_dir)
        assert cb2.should_attempt("weather") is False

    def test_independent_sources(self, tmp_state_dir):
        cb = CircuitBreaker(max_failures=2, state_dir=tmp_state_dir)
        cb.record_failure("weather")
        cb.record_failure("weather")
        assert cb.should_attempt("weather") is False
        assert cb.should_attempt("events") is True

    def test_corrupted_state_file(self, tmp_state_dir):
        path = Path(tmp_state_dir) / "dashboard_breaker_state.json"
        path.write_text("not json")
        cb = CircuitBreaker(state_dir=tmp_state_dir)
        assert cb.should_attempt("weather") is True
