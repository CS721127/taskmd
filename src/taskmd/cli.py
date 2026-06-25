"""
Command Line Interface for TaskMD Lite.

Supports two modes:
  1. REPL mode: `tm` with no arguments enters interactive loop
  2. Subcommand mode: `tm <command> [args]` for single operations

Full Stage 1 commands:
  Task Ops: add, done, half, todo, rm, rm_done, edit, move
  Metadata: due, start, rem, pri, tag
  Views:    list, sort, today, next, overdue, stats, search
  File:     open, validate, reload, archive
  System:   config show, config edit, doctor, migrate, help, exit
"""
import argparse
import sys
import subprocess
import os
import shlex
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from taskmd import __version__
from taskmd.config import load_config, get_config_summary, init_default_config, get_config_file
from taskmd.repository import TaskRepository
from taskmd.service import TaskService
from taskmd.exceptions import TaskNotFoundError, TaskMDError
from taskmd.id_utils import short_id


# ─── Utility ─────────────────────────────────────────────────────────────────


def get_time_left(due: str) -> str:
    """Format time remaining until due date/time.

    Shows whole days ("3d left") for date-only due values, or "Xd Yh" / "Yh Zm"
    precision once the due value carries an HH:MM time component
    (TODOs.md Issue 5).
    """
    if not due:
        return ""
    from taskmd.datetime_utils import parse_task_datetime, has_time_component, format_remaining
    due_dt = parse_task_datetime(due)
    if due_dt is None:
        return "\033[91m(Invalid Date)\033[0m"

    precise = has_time_component(due)
    now_dt = datetime.now()
    days_for_color = (due_dt.date() - now_dt.date()).days
    # For date-only values, "past" means the calendar date has passed (not
    # merely that midnight of today has elapsed). For precise values, "past"
    # means the exact due moment has elapsed.
    is_past = (days_for_color < 0) if not precise else (due_dt < now_dt)
    label = format_remaining(due, now_dt).lstrip("-")

    if is_past:
        if precise:
            return f"\033[91m(OVERDUE {label} ago)\033[0m"
        return "\033[91m(OVERDUE)\033[0m"
    if days_for_color == 0 and not precise:
        return "\033[91m(DUE TODAY)\033[0m"
    if days_for_color <= 3:
        return f"\033[91m(⏳ {label} left)\033[0m"
    elif days_for_color <= 7:
        return f"\033[93m(⏳ {label} left)\033[0m"
    return f"\033[90m(⏳ {label} left)\033[0m"


def is_valid_date(date_str: str) -> bool:
    """Check if a string is a valid YYYY-MM-DD or YYYY-MM-DD HH:MM date."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M"):
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False


def parse_flexible_date(date_str: str) -> str:
    """Parse a flexible date input into YYYY-MM-DD (or YYYY-MM-DD HH:MM).

    Supports: YYYY-MM-DD, YYYY-MM-DD HH:MM, today, tomorrow, yesterday,
    mon-sun, next-mon through next-sun, next-week, 2-weeks, 3-weeks, +Nd.
    Returns the original string if it's already a valid date.
    """
    stripped = date_str.strip()
    # Already valid date?
    if is_valid_date(stripped):
        return stripped
    # Use quick_capture date parser for shorthands
    from taskmd.quick_capture import _parse_date_token
    result = _parse_date_token(stripped)
    if result:
        return result
    return stripped  # return as-is, caller can validate


def format_task(t, show_section: bool = False) -> str:
    """Format a task line for terminal display."""
    color = "\033[92m" if t.status == "[x]" else "\033[93m" if t.status == "[-]" else "\033[0m"
    pri_str = f"\033[91m{'*' * t.pri:<5}\033[0m" if t.pri else " " * 5
    rem_info = f"  \033[90m<{t.rem}>\033[0m" if t.rem else ""
    time_left = get_time_left(t.due) if t.due else ""
    time_left_str = f" {time_left}" if time_left else ""
    tags_str = f" \033[35m[{', '.join(t.tags)}]\033[0m" if t.tags else ""
    section_str = f" \033[90m({t.section}/{t.sub})\033[0m" if show_section else ""
    sid = short_id(t.id)
    return f"      \033[94m[{sid}]\033[0m {pri_str} {color}{t.status}\033[0m {t.name}{time_left_str}{tags_str}{rem_info}{section_str}"


# ─── Custom Argparse ─────────────────────────────────────────────────────────

HELP_TEXT = """\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
\033[1m TaskMD Lite — Command Reference\033[0m
\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m

 \033[1mTask Operations\033[0m
   tm add [name] [-s section] [-b sub]       Launch wizard or add inline
   tm done <id>                              Mark as completed [x]
   tm half <id>                              Mark as in-progress [-]
   tm todo <id>                              Mark as undone [ ]
   tm rm <id>                                Delete task
   tm rm_done                                Delete ALL completed tasks
   tm clear                                  Delete ALL tasks (with confirmation)
   tm edit <id> <name>                       Edit task name
   tm move <id> --section <s> --sub <b>      Move task across sections

 \033[1mMetadata\033[0m
   tm due <id> <date>                        Set deadline (YYYY-MM-DD or "YYYY-MM-DD HH:MM")
   tm start <id> <date>                      Set attention start date (same formats as due)
   tm rem <id> <text>                        Set remark
   tm pri <id> <level>                       Set priority (0-5)
   tm tag <id> add <tag>                     Add tag
   tm tag <id> rm <tag>                      Remove tag

 \033[1mTags\033[0m
   tm tags                                   List all tags in use, with counts
   tm tags <name>                            Show all tasks carrying that tag
   tm list --tag <name>                      Filter the task list to one tag

 \033[1mViews\033[0m
   tm list [--sort tree|priority|due|name]   View all tasks
   tm sort [-i|-p|-d|-n]                     Alias for list sorting
   tm today                                  Tasks due today
   tm next [days]                            Tasks due within N days (default: 7)
   tm overdue                                Overdue incomplete tasks
   tm stats                                  Task statistics
   tm search <keyword>                       Search tasks

 \033[1mFile & System\033[0m
   tm open                                   Open tasks.md in editor — feel free to
                                              edit by hand; non-standard formatting
                                              and #tag/!pri/@due-style shortcuts
                                              are recognized and normalized later
   tm validate                               Check file for errors
   tm reload                                 Reload, repairing IDs and normalizing
                                              any non-standard task formatting
                                              (see "tm open" — hand edits welcome)
   tm archive                                Archive completed tasks
   tm config show                            Show current config
   tm config edit                            Open config file in editor
   tm doctor                                 Diagnose environment & dependencies
   tm migrate txt-to-md                      Convert a legacy .txt task file to .md

 \033[1mREPL\033[0m
   tm help                                   Show this help
   tm intro                                  About TaskMD: what it is, author, version
   tm -v / --version                         Show installed taskmd version
   tm exit                                   Save and quit

 \033[1mQuick Capture\033[0m   (Phase 7 — inline tokens)
   tm add "Write report #work !3 @2026-04-25"
   tm add "Buy milk #errand @tomorrow"
   tm add "Review PR !2 @+3d /Work //Docs [check CI first]"
   tm add "Standup #work @tomorrowT09:30"           (precise due time)
     Tokens: #tag  !priority(1-5)  @due-date  ^start-date  /section  //sub  [note]
     Dates:  @today @tomorrow @mon…@sun @+Nd YYYY-MM-DD
     Precise time: append T HH:MM to any date token, e.g. @tomorrowT14:30

 \033[1mDashboard\033[0m   (Phase 5 — terminal mode benefits from: pip install 'taskmd[ui]')
   tm dashboard                              Terminal dashboard (same as "dashboard cli")
   tm dashboard cli                          Terminal dashboard, explicit
   tm dashboard cli --watch                  Terminal dashboard, auto-refresh on file save
   tm dashboard cli --progress               Section progress bars only
   tm dashboard web   (or: --live)           Open the browser control panel — full feature
                                              parity with the CLI, not a reduced view:
                                                - add tasks (Enter = same quick-capture
                                                  grammar as "tm add", incl. #tag !pri
                                                  @due /section //sub)
                                                - click checkbox to cycle status
                                                - edit name, due, priority, tags inline
                                                - move a task to another section/sub
                                                - delete a single task
                                                - bulk: delete all done, archive done,
                                                  clear everything (with confirmation)
                                                - search, filter by tag, validate the file
                                              [--port N] [--no-browser]

 \033[1mExport\033[0m   (Phase 8)
   tm export csv    [--output f.csv]         Export to CSV
   tm export json   [--output f.json]        Export to JSON
   tm export html   [--output board.html]    Export HTML kanban board  [--theme light|dark] [--group-by status|section|sub]
   tm export svg    [--output board.svg]     Export static SVG board   [--theme light|dark]
   tm export png    [--output board.png]     Export PNG image          [--theme dark] [--scale 2.0]
   tm export pdf    [--output report.pdf]    Export PDF report         [--month 2026-04]
   tm export ics    [--output tasks.ics]     Export iCalendar          (requires 'taskmd[export]')
   tm export report                          Print daily report
   tm export report --week [--output r.md]   Weekly report
   tm export source [--output path.md]       Copy the live schedule .md source file
   tm export md     [--output path.md]       Alias for "export source"
   tm export txt    [--output path.txt]      Export schedule as simplified plain text

   By default, exports land in the current directory. Set a default
   export folder with: tm config edit  →  export_dir = "/path/to/folder"
   (or env var TASKMD_EXPORT_DIR). Giving --output a path with a folder
   in it (e.g. "backups/board.html") always overrides the default folder.

\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m
"""


class TaskMDParser(argparse.ArgumentParser):
    def __init__(self, interactive=False, *args, **kwargs):
        self.interactive = interactive
        super().__init__(*args, **kwargs)

    def print_usage(self, file=None):
        if file is None:
            file = sys.stdout
        file.write(HELP_TEXT)

    def print_help(self, file=None):
        self.print_usage(file)

    def error(self, message):
        self.print_usage(sys.stdout)
        print(f"\033[91m[!] {message}\033[0m")
        if self.interactive:
            raise ValueError(message)
        else:
            sys.exit(1)

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stdout)
        if self.interactive:
            raise RuntimeError("InteractiveContinue")
        else:
            sys.exit(status)


def get_parser(interactive=False):
    parser = TaskMDParser(interactive=interactive, description="TaskMD Lite CLI")
    parser.add_argument('-v', '--version', action='version', version=f'taskmd {__version__}')
    subparsers = parser.add_subparsers(dest="command")

    # ─ add ─
    p_add = subparsers.add_parser("add")
    p_add.add_argument("name", nargs="?", help="Task name")
    p_add.add_argument("--section", "-s", default="Uncategorized")
    p_add.add_argument("--sub", "-b", default="General")
    p_add.add_argument("--due", "-d", default=None)
    p_add.add_argument("--pri", "-p", type=int, default=None)
    p_add.add_argument("--tags", "-t", default=None)
    p_add.add_argument("--start", default=None)
    p_add.add_argument("--course", default=None)

    # ─ Status changes ─
    for cmd in ["done", "half", "todo", "rm"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("id", help="Task ID")

    # ─ rm_done ─
    subparsers.add_parser("rm_done")

    # ─ clear ─
    subparsers.add_parser("clear")

    # ─ edit ─
    p_edit = subparsers.add_parser("edit")
    p_edit.add_argument("id")
    p_edit.add_argument("name")

    # ─ move ─
    p_move = subparsers.add_parser("move")
    p_move.add_argument("id")
    p_move.add_argument("--section", "-s", default=None)
    p_move.add_argument("--sub", "-b", default=None)

    # ─ Metadata ─
    p_due = subparsers.add_parser("due")
    p_due.add_argument("id")
    p_due.add_argument("date")

    p_start = subparsers.add_parser("start")
    p_start.add_argument("id")
    p_start.add_argument("date")

    p_rem = subparsers.add_parser("rem")
    p_rem.add_argument("id")
    p_rem.add_argument("text")

    p_pri = subparsers.add_parser("pri")
    p_pri.add_argument("id")
    p_pri.add_argument("level", type=int)

    # ─ tag ─
    p_tag = subparsers.add_parser("tag")
    p_tag.add_argument("id")
    p_tag.add_argument("action", choices=["add", "rm"])
    p_tag.add_argument("tag_value")

    # ─ tags (Issue 8: list/filter by tag) ─
    p_tags = subparsers.add_parser("tags")
    p_tags.add_argument("tag", nargs="?", default=None,
                         help="If given, list tasks carrying this tag instead of the tag summary")
    p_tags.add_argument("--sort", choices=["count", "name"], default="count",
                         help="Sort tag summary by frequency (default) or name")

    # ─ list ─
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", choices=["tree", "priority", "due", "name"], default="tree")
    p_list.add_argument("--tag", default=None, help="Only show tasks carrying this tag")

    # ─ sort (alias) ─
    p_sort = subparsers.add_parser("sort")
    p_sort.add_argument("mode", choices=["-i", "-p", "-d", "-n"])

    # ─ Views ─
    subparsers.add_parser("today")

    p_next = subparsers.add_parser("next")
    p_next.add_argument("days", nargs="?", type=int, default=7)

    subparsers.add_parser("overdue")
    subparsers.add_parser("stats")

    # ─ search ─
    p_search = subparsers.add_parser("search")
    p_search.add_argument("keyword")

    # ─ File interactions ─
    subparsers.add_parser("open")
    subparsers.add_parser("validate")
    subparsers.add_parser("reload")
    subparsers.add_parser("archive")

    # ─ config ─
    p_config = subparsers.add_parser("config")
    p_config.add_argument("config_action", choices=["show", "edit"])

    # ─ doctor ─
    subparsers.add_parser("doctor")

    # ─ migrate ─
    p_migrate = subparsers.add_parser("migrate")
    p_migrate.add_argument("migrate_type", choices=["txt-to-md"])

    # ─ dashboard (Phase 5; Issue 4: dashboard -> dashboard cli, --live -> web panel) ─
    p_dashboard = subparsers.add_parser("dashboard")
    p_dashboard.add_argument(
        "mode", nargs="?", default=None, choices=["cli", "web"],
        help="'cli' for the terminal dashboard (default), 'web' to launch the browser control panel"
    )
    p_dashboard.add_argument(
        "--live", action="store_true",
        help="Launch the browser-based control panel (same as 'tm dashboard web')"
    )
    p_dashboard.add_argument("--watch", action="store_true",
                              help="With 'cli': auto-refresh the terminal view when tasks.md changes")
    p_dashboard.add_argument("--wide", action="store_true", help="Force dual-column layout (cli mode)")
    p_dashboard.add_argument("--progress", action="store_true", help="Show section progress bars only (cli mode)")
    p_dashboard.add_argument("--port", type=int, default=None, help="Port for the web control panel")
    p_dashboard.add_argument("--no-browser", action="store_true",
                              help="Don't auto-open a browser tab for the web control panel")

    # ─ export (Phase 8) ─
    p_export = subparsers.add_parser("export")
    p_export.add_argument(
        "format",
        choices=["csv", "json", "ics", "html", "report", "pdf", "svg", "png", "source", "md", "txt"],
        help="Export format",
    )
    p_export.add_argument("--output", "-o", default=None, help="Output file path")
    p_export.add_argument("--pretty", action="store_true", default=True, help="Pretty-print JSON")
    p_export.add_argument("--only-pending", action="store_true", help="Only export pending tasks")
    p_export.add_argument("--theme", choices=["light", "dark"], default="light", help="Visual theme")
    p_export.add_argument("--group-by", choices=["status", "section", "sub"], default="status",
                           help="HTML board column grouping (html export only)")
    p_export.add_argument("--week", action="store_true", help="Generate weekly report")
    p_export.add_argument("--week-offset", type=int, default=0, help="Week offset (0=this week)")
    p_export.add_argument("--month", default=None, help="Filter by month YYYY-MM (pdf only)")
    p_export.add_argument("--scale", type=float, default=2.0, help="PNG scale factor (default 2.0)")

    # ─ REPL ─
    subparsers.add_parser("help")
    subparsers.add_parser("intro")
    subparsers.add_parser("exit")

    return parser


# ─── Add Task Wizard ──────────────────────────────────────────────────────────

def add_task_wizard(service):
    """Interactive task creation wizard."""
    print("\n\033[96m[ADD TASK WIZARD]\033[0m")
    try:
        sec = input("  Section (e.g. School)    : ").strip() or "Inbox"
        sub = input("  Subsection (e.g. DP1093) : ").strip() or "General"

        pri_input = input("  Priority (0-5)           : ").strip()
        pri = None
        if pri_input:
            if pri_input.isdigit() and 0 <= int(pri_input) <= 5:
                pri = int(pri_input)
            elif re.fullmatch(r'\*+', pri_input):
                pri = len(pri_input)
            else:
                print("\033[91m[!] Priority must be 0-5 or '*' chars. Using none.\033[0m")

        name = input("  Task Name                : ").strip()
        if not name:
            print("\033[91m[!] Task name cannot be empty. Aborted.\033[0m")
            return

        due = None
        while True:
            due_input = input("  Due Date (YYYY-MM-DD)    : ").strip()
            if not due_input:
                break
            if is_valid_date(due_input):
                due = due_input
                break
            print("\033[91m  [!] Invalid date format. Try again or leave blank.\033[0m")

        start = None
        start_input = input("  Start Date (YYYY-MM-DD)  : ").strip()
        if start_input and is_valid_date(start_input):
            start = start_input

        tags = None
        tags_input = input("  Tags (comma separated)   : ").strip()
        if tags_input:
            tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]

        rem = input("  Remark                   : ").strip() or None

    except (EOFError, KeyboardInterrupt):
        print("\n\033[93m[INFO] Add task cancelled.\033[0m")
        return

    task = service.add_task(
        name, section=sec, sub=sub, due=due, start=start,
        pri=pri, tags=tags, rem=rem,
    )
    print(f"\033[92m[OK] Task added: [{task.id}] {task.name}\033[0m")


# ─── Display Functions ───────────────────────────────────────────────────────

def display_task_list(tasks, config, sort_mode="tree", title=None):
    """Display tasks in the terminal with formatted output."""
    mode_str = {
        "tree": "TREE VIEW (CATEGORICAL)",
        "priority": "SORT BY PRIORITY",
        "due": "SORT BY DUE DATE",
        "name": "SORT BY NAME",
    }.get(sort_mode, "TASK LIST")

    if title:
        mode_str = title

    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)
    print("\033[96m" + "━" * 80 + "\033[0m")
    print(f" 📂 SOURCE: {config.task_file} | \033[1mMODE: {mode_str}\033[0m")
    print("\033[96m" + "━" * 80 + "\033[0m\n")

    if not tasks:
        print("  \033[90m(No tasks found)\033[0m")
    elif sort_mode == "tree":
        hierarchy = {}
        for t in tasks:
            hierarchy.setdefault(t.section, {}).setdefault(t.sub, []).append(t)
        for sec, subs in hierarchy.items():
            # Section progress
            all_in_sec = [t for sub_tasks in subs.values() for t in sub_tasks]
            done_count = sum(1 for t in all_in_sec if t.status == "[x]")
            total_count = len(all_in_sec)
            progress = f" ({done_count}/{total_count})" if total_count > 0 else ""
            print(f"\033[1m--- {sec}\033[0m\033[90m{progress}\033[0m")
            for sub, tlist in subs.items():
                sub_done = sum(1 for t in tlist if t.status == "[x]")
                sub_total = len(tlist)
                sub_progress = f" ({sub_done}/{sub_total})" if sub_total > 0 else ""
                print(f"    \033[36m-- {sub}\033[0m\033[90m{sub_progress}\033[0m")
                for t in tlist:
                    print(format_task(t))
    else:
        if sort_mode == "priority":
            tasks.sort(key=lambda t: t.pri or 0, reverse=True)
        elif sort_mode == "due":
            tasks.sort(key=lambda t: t.due or "9999-99-99")
        elif sort_mode == "name":
            tasks.sort(key=lambda t: t.name.lower())

        for t in tasks:
            print(format_task(t, show_section=True))

    print("\n" + "─" * 80)
    print(" \033[90mType 'help' for commands list | 'exit' to quit\033[0m")


def display_stats(stats):
    """Display task statistics."""
    print("\n\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1m  📊 TASK STATISTICS\033[0m")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print(f"  Total tasks       : {stats['total']}")
    print(f"  ✅ Completed       : \033[92m{stats['done']}\033[0m")
    print(f"  🔄 In Progress     : \033[93m{stats['in_progress']}\033[0m")
    print(f"  📝 Todo            : {stats['todo']}")
    print(f"  ⚠️  Overdue         : \033[91m{stats['overdue']}\033[0m")
    print(f"  📅 Due Today       : \033[91m{stats['due_today']}\033[0m")
    completed_today = stats.get("completed_today", 0)
    if completed_today:
        print(f"  🎉 Done Today      : \033[92m{completed_today}\033[0m")
    urgent = stats.get("urgent", 0)
    if urgent:
        print(f"  🚨 Urgent          : \033[91m{urgent}\033[0m")
    in_attention = stats.get("in_attention", 0)
    if in_attention:
        print(f"  💎 In Attention    : \033[96m{in_attention}\033[0m")
    print(f"  📈 Completion      : \033[96m{stats['completion_rate']}\033[0m")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")


def display_intro():
    """Display project introduction: what TaskMD is, who made it, and version info.

    Covers TODOs.md Issue 10 — "添加一个简介指令... 介绍这个项目在干什么，
    作者，日期版本等等所有的信息" (add an intro command describing what
    the project does, its authors, version, etc).
    """
    import platform

    print("\n\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1m  📋 TaskMD — Markdown-Native Task Management\033[0m")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")

    print("""
 \033[1mWhat it is\033[0m
   TaskMD treats a plain Markdown file as the database. There's no hidden
   binary format and no server — the .md file you already use in your
   editor (VS Code, Obsidian, Vim, ...) *is* the task list. The CLI is an
   accelerator layered on top, not a gatekeeper: every command just reads
   and rewrites that same readable, version-control-friendly file.

 \033[1mWhy it exists\033[0m
   Most task managers lock your data behind an app or a proprietary
   format. TaskMD inverts that: tasks stay portable, diffable, and
   editable by hand, while the CLI adds the speed of structured queries,
   sorting, exports, and a live dashboard on top — best of both worlds.

 \033[1mWho it's for\033[0m
   Developers, researchers, students, and anyone who already lives in
   Markdown and wants a minimal but genuinely extensible task workflow,
   without signing up for a SaaS product.
""")

    print(f" \033[1mProject\033[0m")
    print(f"   Name          : taskmd (TaskMD)")
    print(f"   Version       : {__version__}")
    print(f"   License       : MIT")
    print(f"   Authors       : TaskMD Contributors, CS72127")
    print(f"   Language      : Python {platform.python_version()}+ (requires >=3.9)")
    print(f"   Run on        : {platform.system()} {platform.release()}")

    print("""
 \033[1mLearn more\033[0m
   tm help          → full command reference
   tm doctor         → check your environment & optional dependencies
   tm config show    → see where your data and config files live
""")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")


def display_doctor(config):
    """Display a comprehensive environment diagnostic (TODOs.md Issue 9).

    Checks:
      - Python version & platform
      - Core file paths (task file, config, backup dir, archive)
      - Every optional dependency taskmd can use, grouped by feature area,
        with the exact `pip install` command to fix any that are missing
      - Write permissions on key directories
      - Task file parse health (counts + warnings)
    """
    from taskmd.paths import get_config_dir, get_backup_dir, get_archive_file
    import platform
    import importlib

    config_file = get_config_file()
    backup_dir = get_backup_dir()
    archive_file = get_archive_file()

    print("\n\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1m  🩺 DOCTOR — Environment Diagnostic\033[0m")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")

    print("\n \033[1mSystem\033[0m")
    print(f"  Python       : {platform.python_version()}")
    print(f"  Platform     : {platform.system()} {platform.release()}")
    print(f"  taskmd       : {__version__}")

    print("\n \033[1mFiles & Paths\033[0m")
    print(f"  Task file    : {config.task_file} {'✅' if config.task_file.exists() else '❌ NOT FOUND'}")
    print(f"  Config file  : {config_file} {'✅' if config_file.exists() else '⚠️  (using defaults)'}")
    print(f"  Backup dir   : {backup_dir} {'✅' if backup_dir.exists() else '❌'}")
    print(f"  Archive file : {archive_file} {'✅' if archive_file.exists() else '—'}")
    print(f"  Export dir   : {config.export_dir} {'✅' if Path(config.export_dir).exists() else '❌ NOT FOUND'}")
    print(f"  Editor       : {config.editor}")
    print(f"  Timezone     : {config.timezone}")
    print(f"  Theme        : {config.theme}")

    # Write-permission checks on the directories taskmd actually writes to
    print("\n \033[1mPermissions\033[0m")
    for label, d in (
        ("Task file dir", config.task_file.parent),
        ("Backup dir   ", backup_dir),
        ("Export dir   ", Path(config.export_dir)),
    ):
        if d.exists() and os.access(d, os.W_OK):
            print(f"  {label} : ✅ writable ({d})")
        elif d.exists():
            print(f"  {label} : ❌ NOT writable ({d})")
        else:
            print(f"  {label} : ⚠️  does not exist yet ({d})")

    # ── Dependency checks, grouped by feature area ──────────────────────
    # (module_name, display_name, install_hint)
    dep_groups = [
        ("Dashboard / Live UI  (pip install 'taskmd[ui]')", [
            ("rich", "rich", "taskmd[ui]"),
            ("watchdog", "watchdog", "taskmd[ui]"),
        ]),
        ("Export — Calendar    (pip install 'taskmd[export]')", [
            ("icalendar", "icalendar", "taskmd[export]"),
        ]),
        ("Export — PDF report  (pip install 'taskmd[export]')", [
            ("fpdf", "fpdf2", "taskmd[export]"),
        ]),
        ("Export — SVG/PNG     (pip install 'taskmd[export]')", [
            ("cairosvg", "cairosvg", "taskmd[export]"),
            ("PIL", "Pillow", "taskmd[export]"),
        ]),
        ("Config file (TOML)   (built-in on Python 3.11+)", [
            ("tomllib", "tomllib (stdlib, 3.11+)", None),
            ("tomli", "tomli", "tomli"),
            ("tomli_w", "tomli_w", "tomli_w"),
        ]),
    ]

    missing_any = []
    print("\n \033[1mDependencies\033[0m")
    for group_label, deps in dep_groups:
        print(f"  \033[90m{group_label}\033[0m")
        for module_name, display_name, install_hint in deps:
            try:
                mod = importlib.import_module(module_name)
                version = getattr(mod, "__version__", None)
                ver_str = f" {version}" if version else ""
                print(f"    {display_name:<22}: ✅{ver_str}")
            except ImportError:
                if install_hint:
                    print(f"    {display_name:<22}: ⚠️  not installed  (pip install {install_hint})")
                    missing_any.append((display_name, install_hint))
                else:
                    # e.g. tomllib missing on Python <3.11 but a fallback exists
                    print(f"    {display_name:<22}: —  (not on this Python version; fallback available)")

    if missing_any:
        print(f"\n  \033[93m{len(missing_any)} optional dependenc{'y' if len(missing_any)==1 else 'ies'} missing.\033[0m"
              f" Install everything at once with:")
        print("    \033[1mpip install 'taskmd[all]'\033[0m")
    else:
        print("\n  \033[92mAll optional dependencies are installed.\033[0m")

    # Check task file health
    print("\n \033[1mTask File Health\033[0m")
    if config.task_file.exists():
        try:
            from taskmd.parser import parse_markdown
            content = config.task_file.read_text(encoding="utf-8")
            doc = parse_markdown(content)
            task_count = len(doc.tasks)
            warning_count = len(doc.warnings)
            print(f"  Tasks loaded : \033[92m{task_count}\033[0m")
            if warning_count:
                print(f"  ⚠️  Warnings  : \033[93m{warning_count}\033[0m  (run 'tm validate' for details)")
            else:
                print("  Warnings     : \033[92mnone\033[0m")
        except Exception as e:
            print(f"  Parse status : \033[91mFAILED — {e}\033[0m")
    else:
        print("  \033[93mNo task file yet — it will be created on first 'tm add'.\033[0m")

    print("\n\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")


# ─── Command Handler ─────────────────────────────────────────────────────────

def handle_args(args, service, config, parser):
    """Route parsed arguments to the appropriate handler."""

    try:
        if args.command == "add":
            if not args.name:
                add_task_wizard(service)
            else:
                # ── Quick Capture: parse inline tokens from the name string ──
                from taskmd.quick_capture import parse_quick_capture
                cap = parse_quick_capture(args.name)

                for w in cap.warnings:
                    print(f"\033[93m[!] {w}\033[0m")

                # CLI flags override inline tokens when explicitly provided
                tags = None
                if args.tags:
                    tags = [t.strip().lower() for t in args.tags.split(",")]
                elif cap.tags:
                    tags = cap.tags

                task = service.add_task(
                    cap.name if cap.name else args.name,
                    section=args.section if args.section != "Uncategorized" else (cap.section or args.section),
                    sub=args.sub if args.sub != "General" else (cap.sub or args.sub),
                    due=parse_flexible_date(args.due) if args.due else cap.due,
                    pri=args.pri if args.pri is not None else cap.pri,
                    tags=tags,
                    start=parse_flexible_date(args.start) if args.start else cap.start,
                    course=args.course,
                    rem=cap.rem,
                )
                print(f"\033[92m[OK] Task added: [{task.id}] {task.name}\033[0m")
                if cap.due and not args.due:
                    print(f"     due={cap.due}", end="")
                if cap.pri and args.pri is None:
                    print(f"  pri={cap.pri}", end="")
                if cap.tags and not args.tags:
                    print(f"  tags={cap.tags}", end="")
                # end inline summary line if anything was printed
                has_inline = (cap.due and not args.due) or (cap.pri and args.pri is None) or (cap.tags and not args.tags)
                if has_inline:
                    print()

        elif args.command == "done":
            service.change_status(args.id, "[x]")
            print("\033[92m[OK] Status → [x] completed.\033[0m")

        elif args.command == "half":
            service.change_status(args.id, "[-]")
            print("\033[92m[OK] Status → [-] in progress.\033[0m")

        elif args.command == "todo":
            service.change_status(args.id, "[ ]")
            print("\033[92m[OK] Status → [ ] todo.\033[0m")

        elif args.command == "rm":
            service.remove_task(args.id)
            print("\033[92m[OK] Task removed.\033[0m")

        elif args.command == "rm_done":
            count = service.remove_done()
            if count == 0:
                print("\033[93m[INFO] No completed tasks to remove.\033[0m")
            else:
                print(f"\033[92m[OK] Removed {count} completed task(s).\033[0m")

        elif args.command == "clear":
            print("\033[91m⚠️  WARNING: You are about to clear ALL tasks from your file.\033[0m")
            confirm = input("Are you sure? (type 'yes' to confirm): ").strip().lower()
            if confirm == "yes":
                service.clear_all()
                print("\033[92m[OK] All tasks cleared.\033[0m")
            else:
                print("\033[93m[INFO] Clear cancelled.\033[0m")

        elif args.command == "edit":
            service.edit_name(args.id, args.name)
            print("\033[92m[OK] Name updated.\033[0m")

        elif args.command == "move":
            if not args.section and not args.sub:
                print("\033[91m[!] Specify at least --section or --sub.\033[0m")
            else:
                service.move_task(args.id, section=args.section, sub=args.sub)
                print("\033[92m[OK] Task moved.\033[0m")

        elif args.command == "due":
            d = parse_flexible_date(args.date)
            if not is_valid_date(d):
                print(f"\033[91m[!] Invalid date format: {args.date}\033[0m")
            else:
                service.set_metadata(args.id, "due", d)
                print("\033[92m[OK] Due date updated.\033[0m")

        elif args.command == "start":
            d = parse_flexible_date(args.date)
            if not is_valid_date(d):
                print(f"\033[91m[!] Invalid date format: {args.date}\033[0m")
            else:
                service.set_metadata(args.id, "start", d)
                print("\033[92m[OK] Start date updated.\033[0m")

        elif args.command == "rem":
            service.set_metadata(args.id, "rem", args.text)
            print("\033[92m[OK] Remark updated.\033[0m")

        elif args.command == "pri":
            service.set_metadata(args.id, "pri", args.level)
            print("\033[92m[OK] Priority updated.\033[0m")

        elif args.command == "tag":
            service.set_tags(args.id, args.action, args.tag_value)
            action_str = "added" if args.action == "add" else "removed"
            print(f"\033[92m[OK] Tag '{args.tag_value}' {action_str}.\033[0m")

        elif args.command == "tags":
            if args.tag:
                # Show tasks carrying this specific tag
                matches = service.get_tasks_by_tag(args.tag)
                if not matches:
                    print(f"\033[93m[INFO] No tasks tagged '#{args.tag}'.\033[0m")
                else:
                    print(f"\n\033[1m  🏷  Tasks tagged #{args.tag} ({len(matches)}):\033[0m")
                    for t in matches:
                        print(format_task(t, show_section=True))
            else:
                # Summary view: every tag in use, with counts
                tag_counts = service.get_all_tags()
                if not tag_counts:
                    print("\033[93m[INFO] No tags in use yet. Add one with: tm tag <id> add <tag>\033[0m")
                else:
                    items = list(tag_counts.items())
                    if args.sort == "name":
                        items.sort(key=lambda kv: kv[0].lower())
                    print(f"\n\033[1m  🏷  Tags in use ({len(items)}):\033[0m")
                    width = max(len(name) for name, _ in items) + 2
                    for name, count in items:
                        bar = "█" * min(count, 30)
                        print(f"      \033[35m#{name:<{width}}\033[0m {count:>3}  \033[90m{bar}\033[0m")
                    print("\n      \033[90mtm tags <name>   → show tasks with that tag\033[0m")

        elif args.command in ("list", "sort"):
            sort_mode = "tree"
            if args.command == "sort":
                sort_map = {"-i": "tree", "-p": "priority", "-d": "due", "-n": "name"}
                sort_mode = sort_map.get(args.mode, "tree")
            elif args.command == "list":
                sort_mode = args.sort

            tasks = service.get_all_tasks()
            tag_filter = getattr(args, "tag", None)
            if tag_filter:
                tasks = [
                    t for t in tasks
                    if t.tags and any(tag_filter.lower() == tg.lower() for tg in t.tags)
                ]
                if not tasks:
                    print(f"\033[93m[INFO] No tasks tagged '#{tag_filter}'.\033[0m")
                    return
            display_task_list(tasks, config, sort_mode)

        elif args.command == "today":
            tasks = service.get_today()
            if not tasks:
                print("\n\033[92m  ✅ No tasks due today. You're free!\033[0m")
            else:
                print(f"\n\033[1m  📅 Due Today ({len(tasks)} task(s)):\033[0m")
                for t in tasks:
                    print(format_task(t, show_section=True))

        elif args.command == "next":
            days = args.days
            tasks = service.get_next(days)
            if not tasks:
                print(f"\n\033[92m  ✅ No tasks due in the next {days} days.\033[0m")
            else:
                print(f"\n\033[1m  📅 Due in next {days} days ({len(tasks)} task(s)):\033[0m")
                for t in tasks:
                    print(format_task(t, show_section=True))

        elif args.command == "overdue":
            tasks = service.get_overdue()
            if not tasks:
                print("\n\033[92m  ✅ No overdue tasks!\033[0m")
            else:
                print(f"\n\033[1m  ⚠️  Overdue ({len(tasks)} task(s)):\033[0m")
                for t in tasks:
                    print(format_task(t, show_section=True))

        elif args.command == "stats":
            stats = service.get_stats()
            display_stats(stats)

        elif args.command == "search":
            tasks = service.search(args.keyword)
            if not tasks:
                print(f"\n\033[93m  No tasks matching '{args.keyword}'.\033[0m")
            else:
                print(f"\n\033[1m  🔍 Search: '{args.keyword}' ({len(tasks)} result(s)):\033[0m")
                for t in tasks:
                    print(format_task(t, show_section=True))

        elif args.command == "open":
            print(f"Opening {config.task_file}...")
            editor = config.editor or os.environ.get("EDITOR", "nano")
            subprocess.run([editor, str(config.task_file)])

        elif args.command == "validate":
            errors = service.validate()
            if not errors:
                print("\033[92m[OK] Validation passed — no issues found.\033[0m")
            else:
                print(f"\033[93m[WARN] {len(errors)} issue(s) found:\033[0m")
                for err in errors:
                    print(f"  ⚠️  {err}")

        elif args.command == "reload":
            tasks = service.get_all_tasks()
            print(f"\033[92m[OK] Reloaded. {len(tasks)} task(s), IDs repaired.\033[0m")

        elif args.command == "archive":
            count = service.archive_done(config.archive_file)
            if count == 0:
                print("\033[93m[INFO] No completed tasks to archive.\033[0m")
            else:
                print(f"\033[92m[OK] Archived {count} completed task(s) → {config.archive_file}\033[0m")

        elif args.command == "config":
            if args.config_action == "show":
                print(get_config_summary())
            elif args.config_action == "edit":
                config_file = get_config_file()
                if not config_file.exists():
                    init_default_config()
                    print(f"\033[92m[OK] Default config created at {config_file}\033[0m")
                editor = config.editor or os.environ.get("EDITOR", "nano")
                subprocess.run([editor, str(config_file)])

        elif args.command == "doctor":
            display_doctor(config)

        elif args.command == "migrate":
            if args.migrate_type == "txt-to-md":
                txt_file_path = input("Enter path to legacy txt file to migrate: ").strip()
                if not txt_file_path:
                    print("\033[91m[!] No file path provided. Cancelled.\033[0m")
                else:
                    path_obj = Path(txt_file_path).expanduser().resolve()
                    try:
                        count = service.migrate_txt_to_md(path_obj)
                        print(f"\033[92m[OK] Successfully migrated {count} tasks from TXT to MD format into 'Migrated/Legacy'.\033[0m")
                    except Exception as e:
                        print(f"\033[91m[!] Migration failed: {e}\033[0m")

        elif args.command == "help":
            parser.print_help()

        elif args.command == "intro":
            display_intro()

        elif args.command == "exit":
            sys.exit(0)

        # ── Phase 5: Dashboard ────────────────────────────────────────────
        elif args.command == "dashboard":
            _handle_dashboard(args, service, config)

        # ── Phase 8: Export ───────────────────────────────────────────────
        elif args.command == "export":
            _handle_export(args, service, config)

    except TaskNotFoundError as e:
        print(f"\033[91m[!] {e}\033[0m")
    except TaskMDError as e:
        print(f"\033[91m[!] {e}\033[0m")


# ─── Phase 5: Dashboard Handler ──────────────────────────────────────────────

def _handle_dashboard(args, service, config):
    """Handle the `tm dashboard [cli|web]` command (TODOs.md Issue 4).

    - `tm dashboard` / `tm dashboard cli`  → terminal dashboard (Rich, or ANSI
      fallback). Add --watch to auto-refresh in place when tasks.md changes
      (this is the old `--live` terminal behaviour, renamed since --live now
      means the browser control panel).
    - `tm dashboard web` / `tm dashboard --live` → launches a real browser-based
      control panel (works with zero extra dependencies — stdlib only).
    """
    web_requested = (getattr(args, "mode", None) == "web") or getattr(args, "live", False)

    if web_requested:
        from taskmd.ui.webpanel import run_web_panel
        run_web_panel(
            service,
            port=getattr(args, "port", None),
            open_browser=not getattr(args, "no_browser", False),
        )
        return

    # ── CLI (terminal) dashboard ───────────────────────────────────────────
    from taskmd.ui.dashboard import get_dashboard, RICH_AVAILABLE

    tasks = service.get_all_tasks()
    stats = service.get_stats()
    dashboard = get_dashboard()

    if getattr(args, "progress", False):
        dashboard.render_section_progress(tasks)
        return

    if getattr(args, "watch", False):
        from taskmd.ui.live import run_live_dashboard

        if not RICH_AVAILABLE:
            print("\033[93m[WARN] rich not installed. Using ANSI fallback.\033[0m")

        def render_fn():
            nonlocal tasks, stats
            tasks = service.get_all_tasks()
            stats = service.get_stats()
            if RICH_AVAILABLE:
                from rich.panel import Panel
                from rich.console import Console
                from io import StringIO
                from taskmd.ui.dashboard import RichDashboard

                d = RichDashboard()
                buf = Console(file=StringIO(), highlight=False)
                d.console = buf
                d.render_full(tasks, stats)
                return Panel(buf.file.getvalue(), title="[bold cyan]TaskMD Live[/bold cyan]")
            else:
                dashboard.render_full(tasks, stats)

        if RICH_AVAILABLE:
            run_live_dashboard(config.task_file, render_fn)
        else:
            import os, time
            print(f"Watching: {config.task_file}  (Ctrl+C to exit)")
            last_mtime = config.task_file.stat().st_mtime if config.task_file.exists() else 0
            try:
                dashboard.render_full(tasks, stats)
                while True:
                    time.sleep(0.5)
                    try:
                        mtime = config.task_file.stat().st_mtime
                    except FileNotFoundError:
                        continue
                    if mtime != last_mtime:
                        last_mtime = mtime
                        os.system("clear" if os.name != "nt" else "cls")
                        tasks = service.get_all_tasks()
                        stats = service.get_stats()
                        dashboard.render_full(tasks, stats)
            except KeyboardInterrupt:
                print("\nDashboard closed.")
        return

    dashboard.render_full(tasks, stats)


# ─── Phase 8: Export Handler ──────────────────────────────────────────────────

def _resolve_export_path(filename: str, output: Optional[Path], config) -> Path:
    """Resolve the final path for an export file.

    - If --output was given with a directory component (e.g. "out/board.html"
      or an absolute path), it's honoured exactly as given.
    - If --output was given as a bare filename (e.g. "board.html"), or omitted
      entirely (using the format's default filename), it's placed inside
      config.export_dir (default: current directory; configurable via
      `tm config edit` → export_dir, or TASKMD_EXPORT_DIR) — TODOs.md Issue 7.
    """
    target = output if output is not None else Path(filename)
    if target.is_absolute() or target.parent != Path("."):
        return target
    export_dir = getattr(config, "export_dir", None) or Path.cwd()
    return Path(export_dir) / target.name


def _handle_export_source(args, service, config, fmt: str):
    """Handle `tm export source|md|txt` — export the raw .md schedule file itself
    (optionally converted to plain text), TODOs.md Issue 7.
    """
    from taskmd.exporters.source_exporter import export_source

    as_txt = fmt == "txt"
    default_name = "tasks_source.txt" if as_txt else "tasks_source.md"
    output = Path(args.output) if args.output else None
    target = _resolve_export_path(default_name, output, config)

    source_path = config.task_file
    try:
        export_source(source_path, target, as_txt=as_txt)
    except FileNotFoundError as e:
        print(f"\033[91m[!] {e}\033[0m")
        return

    kind = "Plain-text" if as_txt else "Markdown source"
    print(f"\033[92m[OK] {kind} exported → {target}\033[0m")
    if as_txt:
        print("\033[90m  Converted from markdown: headers, checkboxes, and hidden metadata simplified.\033[0m")
    else:
        print("\033[90m  This is a copy — editing it won't affect your live task file.\033[0m")


def _handle_export(args, service, config):
    """Handle the `tm export <format>` command."""
    tasks = service.get_all_tasks()
    fmt = args.format
    output = Path(args.output) if args.output else None
    only_pending = getattr(args, "only_pending", False)

    if fmt == "csv":
        from taskmd.exporters.csv_exporter import export_csv
        default_out = _resolve_export_path("tasks_export.csv", output, config)
        export_csv(tasks, output_path=default_out, only_pending=only_pending)
        print(f"\033[92m[OK] CSV exported → {default_out}\033[0m")

    elif fmt == "json":
        from taskmd.exporters.json_exporter import export_json
        default_out = _resolve_export_path("tasks_export.json", output, config)
        pretty = getattr(args, "pretty", True)
        export_json(tasks, output_path=default_out, pretty=pretty, only_pending=only_pending)
        print(f"\033[92m[OK] JSON exported → {default_out}\033[0m")

    elif fmt == "ics":
        try:
            from taskmd.exporters.ics_exporter import export_ics
        except ImportError as e:
            print(f"\033[91m[!] {e}\033[0m")
            return
        default_out = _resolve_export_path("tasks.ics", output, config)
        export_ics(tasks, output_path=default_out, only_pending=only_pending)
        print(f"\033[92m[OK] ICS exported → {default_out}\033[0m")
        print("\033[90m  Import this file into Google Calendar, Apple Calendar, or Outlook.\033[0m")

    elif fmt == "html":
        from taskmd.exporters.html_exporter import export_html
        default_out = _resolve_export_path("tasks_board.html", output, config)
        theme = getattr(args, "theme", "light")
        group_by = getattr(args, "group_by", "status")
        export_html(tasks, output_path=default_out, theme=theme, group_by=group_by)
        print(f"\033[92m[OK] HTML board exported → {default_out}\033[0m")
        print("\033[90m  Open in any browser. No server required.\033[0m")

    elif fmt == "report":
        from taskmd.exporters.report import generate_weekly_report, generate_daily_report
        week_offset = getattr(args, "week_offset", 0)
        do_week = getattr(args, "week", False)
        resolved_output = _resolve_export_path(
            "weekly_report.md" if (do_week or week_offset > 0) else "daily_report.md",
            output, config
        ) if output else None

        if do_week or week_offset > 0:
            content = generate_weekly_report(tasks, week_offset=week_offset, output_path=resolved_output)
            if resolved_output:
                print(f"\033[92m[OK] Weekly report exported → {resolved_output}\033[0m")
            else:
                print(content)
        else:
            # Default: print daily report to stdout, optionally save
            from datetime import date
            content = generate_daily_report(tasks, target_date=date.today(), output_path=resolved_output)
            if resolved_output:
                print(f"\033[92m[OK] Daily report exported → {resolved_output}\033[0m")
            else:
                print(content)

    elif fmt == "pdf":
        try:
            from taskmd.exporters.pdf_exporter import export_pdf
        except ImportError as e:
            print(f"\033[91m[!] {e}\033[0m")
            return
        default_out = _resolve_export_path("tasks_report.pdf", output, config)
        month = getattr(args, "month", None)
        export_pdf(
            tasks, output_path=default_out, month=month,
            theme=getattr(args, "theme", "light"),
            only_pending=only_pending,
        )
        print(f"\033[92m[OK] PDF exported → {default_out}\033[0m")
        if month:
            print(f"\033[90m  Filtered to month: {month}\033[0m")

    elif fmt == "svg":
        from taskmd.exporters.image_exporter import export_svg
        default_out = _resolve_export_path("tasks_board.svg", output, config)
        export_svg(tasks, output_path=default_out, theme=getattr(args, "theme", "light"))
        print(f"\033[92m[OK] SVG exported → {default_out}\033[0m")
        print("\033[90m  Open in any browser or vector editor (Inkscape, Figma, etc.)\033[0m")

    elif fmt == "png":
        try:
            from taskmd.exporters.image_exporter import export_png
        except ImportError as e:
            print(f"\033[91m[!] {e}\033[0m")
            return
        default_out = _resolve_export_path("tasks_board.png", output, config)
        scale = getattr(args, "scale", 2.0)
        try:
            export_png(tasks, output_path=default_out,
                       theme=getattr(args, "theme", "light"), scale=scale)
            print(f"\033[92m[OK] PNG exported → {default_out}  (scale={scale})\033[0m")
        except ImportError as e:
            print(f"\033[91m[!] {e}\033[0m")

    elif fmt in ("source", "md", "txt"):
        _handle_export_source(args, service, config, fmt)


# ─── REPL ─────────────────────────────────────────────────────────────────────

def run_repl(service, config):
    """Run the interactive REPL loop."""
    parser = get_parser(interactive=True)

    # Recurring reset check
    needs_action, count = service.check_recurring_tasks()
    if needs_action:
        if count > 0:
            print(f"\n\033[93m[SYSTEM] New cycle detected ({service._today_str()}).\033[0m")
            try:
                ans = input(f"Reset {count} recurring task(s) to incomplete? (y/n): ")
            except (EOFError, KeyboardInterrupt):
                ans = "n"
            if ans.strip().lower() == "y":
                service.apply_recurring_tasks()
                print("\033[92m[OK] Tasks reset for the new cycle.\033[0m")
            else:
                service.skip_recurring_reset()
        else:
            service.skip_recurring_reset()

    # Initial dashboard
    try:
        args_list = parser.parse_args(["list"])
        handle_args(args_list, service, config, parser)
    except Exception:
        pass

    while True:
        try:
            cmd_input = input("\nroot@taskManager:~# ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\033[93m[INFO] Exit via keyboard interrupt.\033[0m")
            break

        if not cmd_input:
            continue

        try:
            args = parser.parse_args(shlex.split(cmd_input))
            handle_args(args, service, config, parser)
        except ValueError:
            pass
        except SystemExit as e:
            if e.code == 0:
                break
        except RuntimeError as e:
            if str(e) == "InteractiveContinue":
                pass
            else:
                raise
        except Exception as e:
            print(f"\033[91m[!] Error: {e}\033[0m")


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    config = load_config()
    repo = TaskRepository(config.task_file)
    service = TaskService(repo)

    if len(sys.argv) == 1:
        run_repl(service, config)
    else:
        # Check for recurring resets before CLI commands (except read-only ones)
        if len(sys.argv) > 1 and sys.argv[1] not in ("list", "stats", "today", "next", "overdue", "search", "config", "validate", "help", "doctor", "tags", "intro"):
            needs_action, count = service.check_recurring_tasks()
            if needs_action:
                if count > 0:
                    print(f"\033[93m[SYSTEM] {count} recurring task(s) reset for new cycle.\033[0m")
                    service.apply_recurring_tasks()
                else:
                    service.skip_recurring_reset()

        parser = get_parser(interactive=False)
        try:
            args = parser.parse_args()
            if args.command:
                handle_args(args, service, config, parser)
        except SystemExit:
            pass


if __name__ == "__main__":
    main()
