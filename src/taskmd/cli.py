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
from datetime import datetime, timedelta

from taskmd.config import load_config, get_config_summary, init_default_config, get_config_file
from taskmd.repository import TaskRepository
from taskmd.service import TaskService
from taskmd.exceptions import TaskNotFoundError, TaskMDError


# ─── Utility ─────────────────────────────────────────────────────────────────

def get_time_left(due: str) -> str:
    """Format time remaining until due date."""
    if not due:
        return ""
    try:
        due_date = datetime.strptime(due, "%Y-%m-%d")
        delta = due_date.date() - datetime.now().date()
        if delta.days < 0:
            return "\033[91m(OVERDUE)\033[0m"
        elif delta.days == 0:
            return "\033[91m(DUE TODAY)\033[0m"
        elif delta.days <= 3:
            return f"\033[91m(⏳ {delta.days}d left)\033[0m"
        elif delta.days <= 7:
            return f"\033[93m(⏳ {delta.days}d left)\033[0m"
        return f"\033[90m(⏳ {delta.days}d left)\033[0m"
    except ValueError:
        return "\033[91m(Invalid Date)\033[0m"


def is_valid_date(date_str: str) -> bool:
    """Check if a string is a valid YYYY-MM-DD date."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_task(t, show_section: bool = False) -> str:
    """Format a task line for terminal display."""
    color = "\033[92m" if t.status == "[x]" else "\033[93m" if t.status == "[-]" else "\033[0m"
    pri_str = f"\033[91m{'*' * t.pri:<5}\033[0m" if t.pri else " " * 5
    rem_info = f"  \033[90m<{t.rem}>\033[0m" if t.rem else ""
    time_left = get_time_left(t.due) if t.due else ""
    time_left_str = f" {time_left}" if time_left else ""
    tags_str = f" \033[35m[{', '.join(t.tags)}]\033[0m" if t.tags else ""
    section_str = f" \033[90m({t.section}/{t.sub})\033[0m" if show_section else ""
    return f"      \033[94m[{t.id}]\033[0m {pri_str} {color}{t.status}\033[0m {t.name}{time_left_str}{tags_str}{rem_info}{section_str}"


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
   tm edit <id> <name>                       Edit task name
   tm move <id> --section <s> --sub <b>      Move task across sections

 \033[1mMetadata\033[0m
   tm due <id> <YYYY-MM-DD>                  Set deadline
   tm start <id> <YYYY-MM-DD>               Set attention start date
   tm rem <id> <text>                        Set remark
   tm pri <id> <level>                       Set priority (0-5)
   tm tag <id> add <tag>                     Add tag
   tm tag <id> rm <tag>                      Remove tag

 \033[1mViews\033[0m
   tm list [--sort tree|priority|due|name]   View all tasks
   tm sort [-i|-p|-d|-n]                     Alias for list sorting
   tm today                                  Tasks due today
   tm next [days]                            Tasks due within N days (default: 7)
   tm overdue                                Overdue incomplete tasks
   tm stats                                  Task statistics
   tm search <keyword>                       Search tasks

 \033[1mFile & System\033[0m
   tm open                                   Open tasks.md in editor
   tm validate                               Check file for errors
   tm reload                                 Reload and repair IDs
   tm archive                                Archive completed tasks
   tm config show                            Show current config
   tm config edit                            Open config file in editor
   tm doctor                                 Diagnose environment

 \033[1mREPL\033[0m
   tm help                                   Show this help
   tm exit                                   Save and quit

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

    # ─ list ─
    p_list = subparsers.add_parser("list")
    p_list.add_argument("--sort", choices=["tree", "priority", "due", "name"], default="tree")

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

    # ─ REPL ─
    subparsers.add_parser("help")
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
    print(f"  Total tasks     : {stats['total']}")
    print(f"  ✅ Completed    : \033[92m{stats['done']}\033[0m")
    print(f"  🔄 In Progress  : \033[93m{stats['in_progress']}\033[0m")
    print(f"  📝 Todo         : {stats['todo']}")
    print(f"  ⚠️  Overdue      : \033[91m{stats['overdue']}\033[0m")
    print(f"  📅 Due Today    : \033[91m{stats['due_today']}\033[0m")
    print(f"  📈 Completion   : \033[96m{stats['completion_rate']}\033[0m")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")


def display_doctor(config):
    """Display environment diagnostic info."""
    from taskmd.paths import get_config_dir, get_backup_dir, get_archive_file
    import platform

    config_file = get_config_file()
    backup_dir = get_backup_dir()
    archive_file = get_archive_file()

    print("\n\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1m  🩺 DOCTOR — Environment Diagnostic\033[0m")
    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print(f"  Python       : {platform.python_version()}")
    print(f"  Platform     : {platform.system()} {platform.release()}")
    print(f"  Task file    : {config.task_file} {'✅' if config.task_file.exists() else '❌ NOT FOUND'}")
    print(f"  Config file  : {config_file} {'✅' if config_file.exists() else '⚠️  (using defaults)'}")
    print(f"  Backup dir   : {backup_dir} {'✅' if backup_dir.exists() else '❌'}")
    print(f"  Archive file : {archive_file} {'✅' if archive_file.exists() else '—'}")
    print(f"  Editor       : {config.editor}")
    print(f"  Timezone     : {config.timezone}")
    print(f"  Theme        : {config.theme}")

    # Check task file health
    if config.task_file.exists():
        try:
            from taskmd.parser import parse_markdown
            content = config.task_file.read_text(encoding="utf-8")
            doc = parse_markdown(content)
            task_count = len(doc.tasks)
            warning_count = len(doc.warnings)
            print(f"  Tasks loaded : \033[92m{task_count}\033[0m")
            if warning_count:
                print(f"  ⚠️  Warnings  : \033[93m{warning_count}\033[0m")
        except Exception as e:
            print(f"  Parse status : \033[91mFAILED — {e}\033[0m")

    print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")


# ─── Command Handler ─────────────────────────────────────────────────────────

def handle_args(args, service, config, parser):
    """Route parsed arguments to the appropriate handler."""

    try:
        if args.command == "add":
            if not args.name:
                add_task_wizard(service)
            else:
                tags = None
                if args.tags:
                    tags = [t.strip().lower() for t in args.tags.split(",")]
                task = service.add_task(
                    args.name,
                    section=args.section,
                    sub=args.sub,
                    due=args.due,
                    pri=args.pri,
                    tags=tags,
                    start=args.start,
                    course=args.course,
                )
                print(f"\033[92m[OK] Task added: [{task.id}] {task.name}\033[0m")

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
            if not is_valid_date(args.date):
                print("\033[91m[!] Invalid date format. Must be YYYY-MM-DD.\033[0m")
            else:
                service.set_metadata(args.id, "due", args.date)
                print("\033[92m[OK] Due date updated.\033[0m")

        elif args.command == "start":
            if not is_valid_date(args.date):
                print("\033[91m[!] Invalid date format. Must be YYYY-MM-DD.\033[0m")
            else:
                service.set_metadata(args.id, "start", args.date)
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

        elif args.command in ("list", "sort"):
            sort_mode = "tree"
            if args.command == "sort":
                sort_map = {"-i": "tree", "-p": "priority", "-d": "due", "-n": "name"}
                sort_mode = sort_map.get(args.mode, "tree")
            elif args.command == "list":
                sort_mode = args.sort

            tasks = service.get_all_tasks()
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

        elif args.command == "exit":
            sys.exit(0)

    except TaskNotFoundError as e:
        print(f"\033[91m[!] {e}\033[0m")
    except TaskMDError as e:
        print(f"\033[91m[!] {e}\033[0m")


# ─── REPL ─────────────────────────────────────────────────────────────────────

def run_repl(service, config):
    """Run the interactive REPL loop."""
    parser = get_parser(interactive=True)

    # Daily reset check
    is_new_day, daily_count = service.check_daily_reset()
    if is_new_day and daily_count > 0:
        print(f"\n\033[93m[SYSTEM] New day detected ({service._today_str()}).\033[0m")
        try:
            ans = input(f"Reset {daily_count} 'Daily' task(s) to incomplete? (y/n): ")
        except (EOFError, KeyboardInterrupt):
            ans = "n"
        if ans.strip().lower() == "y":
            service.reset_daily_tasks()
            print("\033[92m[OK] Daily tasks reset.\033[0m")
        else:
            service.skip_daily_reset()
    elif is_new_day:
        service.skip_daily_reset()

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
        parser = get_parser(interactive=False)
        try:
            args = parser.parse_args()
            if args.command:
                handle_args(args, service, config, parser)
        except SystemExit:
            pass


if __name__ == "__main__":
    main()
