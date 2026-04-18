"""
Live Reload for TaskMD Dashboard.

Uses `watchdog` to monitor tasks.md for file changes.
When a change is detected, reloads and re-renders the dashboard.

Requires: pip install 'taskmd[ui]'
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional, Callable

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class TaskFileHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Watchdog event handler for tasks.md changes."""

    def __init__(self, task_file: Path, on_change: Callable):
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.task_file = task_file
        self.on_change = on_change
        self._last_trigger = 0.0
        self._debounce_secs = 0.5

    def on_modified(self, event):
        # Only react to the specific task file
        if Path(event.src_path).resolve() == self.task_file.resolve():
            now = time.time()
            if now - self._last_trigger > self._debounce_secs:
                self._last_trigger = now
                self.on_change()


def run_live_dashboard(task_file: Path, render_fn: Callable, interval: float = 0.5):
    """
    Run the dashboard in live-reload mode.

    Args:
        task_file: Path to tasks.md being watched.
        render_fn: Callable that takes no args and renders the dashboard.
                   Should return a Rich renderable if using Rich.
        interval: Polling interval fallback in seconds.
    """
    if not RICH_AVAILABLE:
        _run_ansi_live(task_file, render_fn, interval)
        return

    console = Console()

    if not WATCHDOG_AVAILABLE:
        console.print(
            "[yellow]watchdog not installed — falling back to polling.[/yellow]\n"
            "[dim]Run: pip install 'taskmd[ui]' for file-event based reload.[/dim]"
        )
        _run_polling_live(task_file, render_fn, interval, console)
        return

    _run_watchdog_live(task_file, render_fn, console)


def _run_watchdog_live(task_file: Path, render_fn: Callable, console):
    """Live mode backed by watchdog file events."""
    from rich.live import Live

    should_reload = {"flag": False}

    def trigger_reload():
        should_reload["flag"] = True

    handler = TaskFileHandler(task_file, trigger_reload)
    observer = Observer()
    observer.schedule(handler, str(task_file.parent), recursive=False)
    observer.start()

    console.print(
        f"[cyan]👁  Watching:[/cyan] [dim]{task_file}[/dim]  "
        f"[dim]Press Ctrl+C to exit[/dim]"
    )

    try:
        # Initial render
        renderable = render_fn()
        with Live(renderable, console=console, refresh_per_second=4, screen=True) as live:
            while True:
                time.sleep(0.25)
                if should_reload["flag"]:
                    should_reload["flag"] = False
                    try:
                        renderable = render_fn()
                        live.update(renderable)
                    except Exception as e:
                        from rich.panel import Panel
                        live.update(
                            Panel(f"[red]Error reloading:[/red] {e}", border_style="red")
                        )
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        console.print("\n[dim]Dashboard closed.[/dim]")


def _run_polling_live(task_file: Path, render_fn: Callable, interval: float, console):
    """Fallback polling mode when watchdog is unavailable."""
    last_mtime = task_file.stat().st_mtime if task_file.exists() else 0

    console.print(
        f"[cyan]👁  Polling:[/cyan] [dim]{task_file}[/dim] every {interval}s  "
        f"[dim]Press Ctrl+C to exit[/dim]"
    )

    try:
        render_fn()
        while True:
            time.sleep(interval)
            try:
                mtime = task_file.stat().st_mtime
            except FileNotFoundError:
                continue

            if mtime != last_mtime:
                last_mtime = mtime
                # Clear and re-render
                os.system("clear" if os.name != "nt" else "cls")
                try:
                    render_fn()
                except Exception as e:
                    console.print(f"[red]Reload error:[/red] {e}")
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard closed.[/dim]")


def _run_ansi_live(task_file: Path, render_fn: Callable, interval: float):
    """Plain ANSI fallback without rich."""
    last_mtime = task_file.stat().st_mtime if task_file.exists() else 0

    print(f"Watching: {task_file}  (Ctrl+C to exit)")

    try:
        render_fn()
        while True:
            time.sleep(interval)
            try:
                mtime = task_file.stat().st_mtime
            except FileNotFoundError:
                continue

            if mtime != last_mtime:
                last_mtime = mtime
                os.system("clear" if os.name != "nt" else "cls")
                try:
                    render_fn()
                except Exception as e:
                    print(f"Reload error: {e}")
    except KeyboardInterrupt:
        print("\nDashboard closed.")
