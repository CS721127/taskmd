"""
Unit tests for recurrence logic.
"""
from datetime import date
from taskmd.recurrence import parse_recur, should_trigger
from taskmd.models import Task

def test_daily_recurrence():
    spec = parse_recur("daily")
    # task done yesterday, last run yesterday -> should reset today
    today = date(2026, 4, 11)
    last_run = date(2026, 4, 10)
    assert should_trigger(spec, last_run, today) is True
    
    # same day -> no trigger
    assert should_trigger(spec, today, today) is False

def test_weekly_recurrence():
    # April 13, 2026 is Monday
    spec = parse_recur("weekly-mon")
    
    last_run = date(2026, 4, 12) # Sunday
    today = date(2026, 4, 13) # Monday
    assert should_trigger(spec, last_run, today) is True
    
    # Not Monday yet
    today = date(2026, 4, 12) # Sunday
    last_run = date(2026, 4, 11) # Saturday
    assert should_trigger(spec, last_run, today) is False

def test_monthly_recurrence():
    spec = parse_recur("monthly-1")
    
    last_run = date(2026, 3, 31)
    today = date(2026, 4, 1) # First of month
    assert should_trigger(spec, last_run, today) is True
    
    # Same month, not trigger
    today = date(2026, 3, 31)
    last_run = date(2026, 3, 30)
    assert should_trigger(spec, last_run, today) is False

def test_parse_recur_variations():
    assert parse_recur("daily").type == "daily"
    assert parse_recur("weekly-fri").value == "fri"
    assert parse_recur("monthly-15").value == "15"
    assert parse_recur("invalid") is None
