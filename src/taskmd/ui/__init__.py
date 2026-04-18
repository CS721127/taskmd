"""
TaskMD UI package.

Provides Rich-powered dashboard and live-reload capabilities.
Falls back gracefully to ANSI output when rich/watchdog are unavailable.
"""
from taskmd.ui.heatmap import get_urgency_level, get_rich_style, get_ansi_color
from taskmd.ui.dashboard import get_dashboard, RICH_AVAILABLE
from taskmd.ui.live import run_live_dashboard, WATCHDOG_AVAILABLE

__all__ = [
    "get_urgency_level",
    "get_rich_style",
    "get_ansi_color",
    "get_dashboard",
    "RICH_AVAILABLE",
    "run_live_dashboard",
    "WATCHDOG_AVAILABLE",
]
