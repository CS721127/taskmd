"""
Rich Dashboard for TaskMD.

Renders the full task view using the `rich` library.
Falls back gracefully to ANSI mode if rich is not installed.

Features:
  - Section progress bars (✅ 3/7 ████░░░░░░ 43%)
  - Heatmap color coding per urgency level
  - Dual-column layout for wide terminals (>120 cols)
  - Single-column compact mode for narrow terminals (<80 cols)
  - Unified status panel at the bottom
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Optional

from taskmd.models import Task
from taskmd.ui.heatmap import (
    get_urgency_level, get_rich_style, get_urgency_icon,
    URGENCY_OVERDUE, URGENCY_DUE_TODAY,
    URGENCY_DUE_SOON, URGENCY_DUE_UPCOMING
)

# ─── Rich import (optional) ──────────────────────────────────────────────────

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.progress import Progress, BarColumn, TextColumn, MofNCompleteColumn
    from rich.text import Text
    from rich.rule import Rule
    from rich.style import Style
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _group_by_section(tasks: List[Task]) -> Dict[str, Dict[str, List[Task]]]:
    """Group tasks by section → subsection → [tasks]."""
    groups: Dict[str, Dict[str, List[Task]]] = {}
    for task in tasks:
        sec = task.section or "Uncategorized"
        sub = task.sub or "General"
        groups.setdefault(sec, {}).setdefault(sub, []).append(task)
    return groups


def _section_progress(tasks: List[Task]) -> tuple[int, int]:
    """Return (done_count, total_count) for a list of tasks."""
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "[x]")
    return done, total


def _make_progress_bar(done: int, total: int, width: int = 10) -> str:
    """Create a text progress bar like ████░░░░░░ 43%."""
    if total == 0:
        return "░" * width + "  0%"
    ratio = done / total
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    return f"{bar} {pct:3d}%"


def _format_task_row_rich(task: Task, show_section: bool = False) -> "Text":
    """Format a task as a Rich Text object with heatmap coloring."""
    style = get_rich_style(task)
    icon = get_urgency_icon(task)

    # Status symbol
    if task.status == "[x]":
        status_sym = "✅"
    elif task.status == "[-]":
        status_sym = "🔄"
    else:
        status_sym = "☐ "

    # Priority stars
    pri_str = ("★" * task.pri) if task.pri else ""

    # Build the text
    line = Text()
    line.append(f"  {icon} ", style="dim")
    line.append(f"[{task.id}] ", style="bright_blue")
    if pri_str:
        line.append(f"{pri_str:<5} ", style="bold red")
    line.append(f"{status_sym} ", style=style)
    line.append(task.name, style=style)

    if task.due:
        urgency = get_urgency_level(task)
        if urgency in (URGENCY_OVERDUE,):
            line.append(f"  ⚠ {task.due}", style="bold red")
        elif urgency == URGENCY_DUE_TODAY:
            line.append(f"  ⏰ DUE TODAY", style="bold yellow")
        elif urgency in (URGENCY_DUE_SOON, URGENCY_DUE_UPCOMING):
            line.append(f"  📅 {task.due}", style="yellow")
        else:
            line.append(f"  📅 {task.due}", style="dim")

    if task.tags:
        line.append(f"  [{', '.join(task.tags)}]", style="magenta")

    if task.rem:
        line.append(f"  ← {task.rem}", style="dim italic")

    if show_section:
        line.append(f"  ({task.section}/{task.sub})", style="dim")

    return line


# ─── Rich Dashboard ───────────────────────────────────────────────────────────

class RichDashboard:
    """Rich-powered terminal dashboard."""

    def __init__(self):
        if not RICH_AVAILABLE:
            raise ImportError(
                "rich is not installed. Run: pip install 'taskmd[ui]'"
            )
        self.console = Console()

    @property
    def width(self) -> int:
        return self.console.width

    def render_full(
        self,
        tasks: List[Task],
        stats: Dict,
        title: str = "TaskMD Dashboard",
    ):
        """Render the full dashboard to the terminal."""
        self.console.print()
        self.console.print(Rule(f"[bold cyan]{title}[/bold cyan]"))
        self.console.print()

        # Status bar at top
        self._render_status_panel(stats)
        self.console.print()

        # Group tasks
        groups = _group_by_section(tasks)

        if self.width >= 120:
            self._render_dual_column(groups, tasks)
        else:
            self._render_single_column(groups)

        self.console.print()
        self.console.print(Rule(style="dim"))

    def _render_status_panel(self, stats: Dict):
        """Render the top status summary panel."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        total = stats.get("total", 0)
        done = stats.get("done", 0)
        in_progress = stats.get("in_progress", 0)
        todo = stats.get("todo", 0)
        overdue = stats.get("overdue", 0)
        due_today = stats.get("due_today", 0)
        rate = stats.get("completion_rate", "0.0%")

        line = Text()
        line.append(f"📅 {now}   ", style="dim")
        line.append(f"Total: {total}  ", style="white")
        line.append(f"✅ Done: {done}  ", style="green")
        line.append(f"🔄 In Progress: {in_progress}  ", style="yellow")
        line.append(f"☐ Todo: {todo}  ", style="white")

        if overdue > 0:
            line.append(f"🔴 Overdue: {overdue}  ", style="bold red")
        if due_today > 0:
            line.append(f"⏰ Due Today: {due_today}  ", style="bold yellow")

        line.append(f"📊 Rate: {rate}", style="cyan")

        self.console.print(Panel(line, title="[bold]Status[/bold]", border_style="blue"))

    def _render_single_column(self, groups: Dict):
        """Render tasks in single-column mode."""
        for section_name, subs in groups.items():
            all_sec_tasks = [t for sub_tasks in subs.values() for t in sub_tasks]
            done, total = _section_progress(all_sec_tasks)
            bar = _make_progress_bar(done, total)

            section_header = Text()
            section_header.append(f"  {section_name}", style="bold white")
            section_header.append(f"  {bar}", style="green" if done == total else "yellow")

            self.console.print(Panel(section_header, border_style="blue", expand=False))

            for sub_name, sub_tasks in subs.items():
                sub_done, sub_total = _section_progress(sub_tasks)
                sub_bar = _make_progress_bar(sub_done, sub_total, width=6)

                self.console.print(
                    f"    [bold dim]── {sub_name}[/bold dim]  "
                    f"[dim]{sub_bar}[/dim]"
                )

                for task in sub_tasks:
                    self.console.print(_format_task_row_rich(task))

            self.console.print()

    def _render_dual_column(self, groups: Dict, all_tasks: List[Task]):
        """Render tasks in dual-column layout for wide terminals."""
        # Left column: task tree, Right column: today + stats
        left_lines = []
        for section_name, subs in groups.items():
            all_sec_tasks = [t for sub_tasks in subs.values() for t in sub_tasks]
            done, total = _section_progress(all_sec_tasks)
            bar = _make_progress_bar(done, total)

            left_lines.append(
                f"[bold white]{section_name}[/bold white]  "
                f"[{'green' if done == total else 'yellow'}]{bar}[/]"
            )

            for sub_name, sub_tasks in subs.items():
                sub_done, sub_total = _section_progress(sub_tasks)
                left_lines.append(
                    f"  [dim]── {sub_name}[/dim]  "
                    f"[dim]{_make_progress_bar(sub_done, sub_total, 6)}[/dim]"
                )
                for task in sub_tasks:
                    left_lines.append(_format_task_row_rich(task))

        # Right column: today's tasks
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_tasks = [
            t for t in all_tasks
            if t.due == today_str and t.status != "[x]"
        ]
        overdue_tasks = [
            t for t in all_tasks
            if t.due and t.due < today_str and t.status != "[x]"
        ]

        right_lines = [Text("📅 Today", style="bold yellow")]
        if today_tasks:
            for t in today_tasks:
                right_lines.append(_format_task_row_rich(t))
        else:
            right_lines.append(Text("  (none)", style="dim"))

        right_lines.append(Text(""))
        right_lines.append(Text("🔴 Overdue", style="bold red"))
        if overdue_tasks:
            for t in overdue_tasks[:5]:
                right_lines.append(_format_task_row_rich(t))
            if len(overdue_tasks) > 5:
                right_lines.append(Text(f"  ...and {len(overdue_tasks) - 5} more", style="dim"))
        else:
            right_lines.append(Text("  (none)", style="dim green"))

        from rich.live import Live
        from io import StringIO

        # Build left panel content
        left_text = Text()
        for item in left_lines:
            if isinstance(item, Text):
                left_text.append_text(item)
                left_text.append("\n")
            else:
                left_text.append(item + "\n")

        right_text = Text()
        for item in right_lines:
            if isinstance(item, Text):
                right_text.append_text(item)
                right_text.append("\n")
            else:
                right_text.append(str(item) + "\n")

        left_panel = Panel(left_text, title="[bold]Tasks[/bold]", border_style="blue")
        right_panel = Panel(right_text, title="[bold]Quick View[/bold]", border_style="cyan")

        self.console.print(Columns([left_panel, right_panel]))

    def render_section_progress(self, tasks: List[Task]):
        """Render a progress bar for each section."""
        groups = _group_by_section(tasks)

        table = Table(show_header=True, header_style="bold blue", box=None)
        table.add_column("Section", style="white", min_width=20)
        table.add_column("Progress", min_width=20)
        table.add_column("Count", justify="right")

        for section_name, subs in groups.items():
            all_tasks = [t for sub_tasks in subs.values() for t in sub_tasks]
            done, total = _section_progress(all_tasks)
            bar = _make_progress_bar(done, total)
            style = "green" if done == total else ("yellow" if done > 0 else "white")
            table.add_row(
                section_name,
                Text(bar, style=style),
                f"{done}/{total}",
            )

            for sub_name, sub_tasks in subs.items():
                sub_done, sub_total = _section_progress(sub_tasks)
                sub_bar = _make_progress_bar(sub_done, sub_total, width=6)
                sub_style = "green" if sub_done == sub_total else "dim"
                table.add_row(
                    f"  └─ {sub_name}",
                    Text(sub_bar, style=sub_style),
                    f"{sub_done}/{sub_total}",
                )

        self.console.print(table)

    def render_task_table(
        self,
        tasks: List[Task],
        title: str = "Tasks",
        show_section: bool = True,
    ):
        """Render tasks as a Rich table."""
        table = Table(
            title=title,
            show_header=True,
            header_style="bold blue",
            expand=self.width > 100,
        )
        table.add_column("ID", style="bright_blue", width=8)
        table.add_column("Pri", width=5)
        table.add_column("Status", width=4)
        table.add_column("Name", min_width=20)
        table.add_column("Due", width=12)
        table.add_column("Tags", width=15)
        if show_section:
            table.add_column("Section", width=15)

        for task in tasks:
            style = get_rich_style(task)
            icon = get_urgency_icon(task)

            pri_text = Text("★" * task.pri if task.pri else "", style="bold red")
            status_sym = (
                "✅" if task.status == "[x]"
                else "🔄" if task.status == "[-]"
                else "☐"
            )

            due_text = Text()
            if task.due:
                urgency = get_urgency_level(task)
                due_style = (
                    "bold red" if urgency == URGENCY_OVERDUE
                    else "bold yellow" if urgency == URGENCY_DUE_TODAY
                    else "yellow" if urgency in (URGENCY_DUE_SOON, URGENCY_DUE_UPCOMING)
                    else "dim"
                )
                due_text = Text(task.due, style=due_style)

            tags_text = Text(
                ", ".join(task.tags) if task.tags else "",
                style="magenta"
            )

            row_data = [
                f"{icon} {task.id}",
                pri_text,
                status_sym,
                Text(task.name, style=style),
                due_text,
                tags_text,
            ]
            if show_section:
                row_data.append(f"{task.section}/{task.sub}")

            table.add_row(*row_data)

        self.console.print(table)


# ─── ANSI Fallback Dashboard ─────────────────────────────────────────────────

class AnsiFallbackDashboard:
    """Plain ANSI fallback dashboard when rich is not available."""

    def render_full(self, tasks: List[Task], stats: Dict, title: str = "TaskMD Dashboard"):
        """Render a basic ANSI dashboard."""
        from taskmd.ui.heatmap import get_ansi_color, ANSI_RESET

        width = 72
        print("\033[96m" + "━" * width + "\033[0m")
        print(f"\033[1m  {title}\033[0m")
        print("\033[96m" + "━" * width + "\033[0m")

        # Status line
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        total = stats.get("total", 0)
        done = stats.get("done", 0)
        overdue = stats.get("overdue", 0)
        rate = stats.get("completion_rate", "0.0%")
        print(
            f"  📅 {now}  Total:{total}  ✅{done}  "
            + (f"\033[91m🔴Overdue:{overdue}\033[0m  " if overdue else "")
            + f"Rate:{rate}"
        )
        print()

        # Group and display
        groups = _group_by_section(tasks)
        for section_name, subs in groups.items():
            all_sec = [t for sub_tasks in subs.values() for t in sub_tasks]
            sdone, stotal = _section_progress(all_sec)
            bar = _make_progress_bar(sdone, stotal)
            print(f"\033[1;34m  ▶ {section_name}\033[0m  \033[32m{bar}\033[0m")

            for sub_name, sub_tasks in subs.items():
                print(f"    \033[90m── {sub_name}\033[0m")
                for task in sub_tasks:
                    color = get_ansi_color(task)
                    icon = get_urgency_icon(task)
                    status_sym = "✅" if task.status == "[x]" else "🔄" if task.status == "[-]" else "☐ "
                    pri = ("★" * task.pri) if task.pri else ""
                    due = f"  📅{task.due}" if task.due else ""
                    tags = f"  [{','.join(task.tags)}]" if task.tags else ""
                    print(
                        f"      {icon} \033[94m[{task.id}]\033[0m "
                        f"{color}{status_sym} {task.name}\033[0m"
                        f"\033[33m{pri}\033[0m{due}{tags}"
                    )
            print()

        print("\033[96m" + "━" * width + "\033[0m")


def get_dashboard():
    """Get the best available dashboard."""
    if RICH_AVAILABLE:
        return RichDashboard()
    return AnsiFallbackDashboard()
