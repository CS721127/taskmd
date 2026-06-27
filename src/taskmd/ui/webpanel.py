"""
TaskMD Web Control Panel.

A real, browser-based UI for `tm dashboard --live` (TODOs.md Issue 4):
  "dashboard -live 应该可以调出一个控制面板，有UI界面的而不是仅仅CLI"
  (`dashboard --live` should bring up a control panel with an actual UI,
  not just CLI text.)

Implemented entirely with the Python standard library (`http.server`,
`json`, `threading`) so it works even without the optional `taskmd[ui]`
extras — anyone running `tm dashboard --live` gets a real GUI, no extra
installs required.

Full CLI parity (Issue 4 follow-up): the panel exposes essentially every
day-to-day `tm` operation, not just status/due editing —
  - Add a task with full quick-capture syntax (#tag !pri @due /section //sub)
  - Edit name, due, start, priority, reminder note inline
  - Add/remove individual tags
  - Move a task to a different section/subsection
  - Delete a single task
  - Bulk: delete all completed, archive all completed, clear everything
  - Search by keyword, browse/filter by tag
  - Validate the file and see any formatting warnings
So a person using the browser panel gets the same capabilities as the
CLI, not a reduced subset.
"""
from __future__ import annotations

import json
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

from taskmd.models import Task
from taskmd.id_utils import short_id
from taskmd.ui.heatmap import get_urgency_level


def _task_to_dict(task: Task) -> dict:
    """Serialize a Task into the JSON shape the panel's JS expects."""
    return {
        "id": task.id,
        "short_id": short_id(task.id),
        "name": task.name,
        "section": task.section or "Uncategorized",
        "sub": task.sub or "General",
        "status": task.status,
        "due": task.due,
        "start": task.start,
        "pri": task.pri,
        "tags": task.tags or [],
        "rem": task.rem,
        "urgency": get_urgency_level(task),
    }


def _build_payload(service) -> dict:
    """Build the full {tasks, stats, sections, tags} snapshot sent to the browser."""
    tasks = service.get_all_tasks()
    stats = service.get_stats()

    # Seed every section/subsection that exists in the document — including
    # ones with zero tasks — so a freshly created empty section/subsection
    # is visible right away rather than only appearing once it has a task.
    sections: "dict[str, dict[str, list]]" = {}
    for sec, subs in service.get_all_sections().items():
        sections[sec] = {sub: [] for sub in subs}

    for t in tasks:
        sec = t.section or "Uncategorized"
        sub = t.sub or "General"
        sections.setdefault(sec, {}).setdefault(sub, []).append(_task_to_dict(t))

    return {
        "tasks": [_task_to_dict(t) for t in tasks],
        "sections": sections,
        "tags": service.get_all_tags(),
        "stats": {
            "total": stats.get("total", 0),
            "done": stats.get("done", 0),
            "in_progress": stats.get("in_progress", 0),
            "todo": stats.get("todo", 0),
            "overdue": stats.get("overdue", 0),
            "due_today": stats.get("due_today", 0),
            "urgent": stats.get("urgent", 0),
            "completion_rate": stats.get("completion_rate", "0.0%"),
        },
        "task_file": str(service.repo.file_path),
    }


def _find_free_port(preferred: int = 7177) -> int:
    """Pick a free local port, preferring `preferred` if available."""
    for port in (preferred, preferred + 1, preferred + 2, 0):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
        except OSError:
            continue
    return 0


def make_handler(service, html_content: str):
    """Build a request handler class bound to a specific TaskService instance."""

    class PanelHandler(BaseHTTPRequestHandler):
        server_version = "TaskMDPanel/1.0"

        def log_message(self, fmt, *args):
            pass  # silence default request logging — keep the terminal quiet

        # ── helpers ──────────────────────────────────────────────────────
        def _send_json(self, data, status: int = 200):
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str):
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}

        # ── routes ───────────────────────────────────────────────────────
        def do_GET(self):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)

            if parsed.path in ("/", "/index.html"):
                self._send_html(html_content)
            elif parsed.path == "/api/state":
                try:
                    self._send_json(_build_payload(service))
                except Exception as e:
                    self._send_json({"error": str(e)}, status=500)
            elif parsed.path == "/api/validate":
                try:
                    errors = service.validate()
                    self._send_json({"errors": errors})
                except Exception as e:
                    self._send_json({"error": str(e)}, status=500)
            elif parsed.path == "/api/search":
                try:
                    keyword = (qs.get("q") or [""])[0]
                    if not keyword.strip():
                        self._send_json({"results": []})
                        return
                    results = service.search(keyword)
                    self._send_json({"results": [_task_to_dict(t) for t in results]})
                except Exception as e:
                    self._send_json({"error": str(e)}, status=500)
            else:
                self._send_json({"error": "not found"}, status=404)

        def do_POST(self):
            from taskmd.exceptions import TaskNotFoundError, TaskMDError
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            body = self._read_json_body()

            try:
                # /api/tasks  → add a new task, with full quick-capture support
                # (#tag !pri @due ^start /section //sub [note]) so the panel's
                # "press Enter to create" box has the exact same grammar as
                # `tm add "..."` on the command line.
                if parsed.path == "/api/tasks":
                    raw_name = (body.get("name") or "").strip()
                    if not raw_name:
                        self._send_json({"error": "name is required"}, status=400)
                        return

                    from taskmd.quick_capture import parse_quick_capture
                    cap = parse_quick_capture(raw_name)

                    explicit_tags = body.get("tags")
                    tags = explicit_tags if explicit_tags else (cap.tags or None)

                    service.add_task(
                        name=cap.name if cap.name else raw_name,
                        section=body.get("section") or cap.section or "Uncategorized",
                        sub=body.get("sub") or cap.sub or "General",
                        due=body.get("due") or cap.due or None,
                        start=body.get("start") or cap.start or None,
                        pri=body.get("pri") if body.get("pri") is not None else cap.pri,
                        tags=tags,
                        rem=body.get("rem") or cap.rem or None,
                    )
                    payload = _build_payload(service)
                    payload["capture_warnings"] = cap.warnings
                    self._send_json(payload)
                    return

                # /api/tasks/<id>/status  → cycle or set status
                if len(parts) == 4 and parts[0] == "api" and parts[1] == "tasks" and parts[3] == "status":
                    task_id = parts[2]
                    new_status = body.get("status")
                    if new_status not in ("[ ]", "[-]", "[x]"):
                        self._send_json({"error": "invalid status"}, status=400)
                        return
                    service.change_status(task_id, new_status)
                    self._send_json(_build_payload(service))
                    return

                # /api/tasks/<id>/field  → set a single metadata field
                if len(parts) == 4 and parts[0] == "api" and parts[1] == "tasks" and parts[3] == "field":
                    task_id = parts[2]
                    field_name = body.get("field")
                    value = body.get("value")
                    if field_name not in ("due", "start", "rem", "pri", "name", "course", "weight", "recur", "est", "loc"):
                        self._send_json({"error": "field not editable from panel"}, status=400)
                        return
                    service.set_metadata(task_id, field_name, value)
                    self._send_json(_build_payload(service))
                    return

                # /api/tasks/<id>/tags  → add or remove a single tag
                if len(parts) == 4 and parts[0] == "api" and parts[1] == "tasks" and parts[3] == "tags":
                    task_id = parts[2]
                    action = body.get("action")
                    tag = (body.get("tag") or "").strip()
                    if action not in ("add", "rm") or not tag:
                        self._send_json({"error": "action ('add'/'rm') and tag are required"}, status=400)
                        return
                    service.set_tags(task_id, action, tag)
                    self._send_json(_build_payload(service))
                    return

                # /api/tasks/<id>/move  → move to a different section/subsection
                if len(parts) == 4 and parts[0] == "api" and parts[1] == "tasks" and parts[3] == "move":
                    task_id = parts[2]
                    section = body.get("section") or None
                    sub = body.get("sub") or None
                    if not section and not sub:
                        self._send_json({"error": "section and/or sub is required"}, status=400)
                        return
                    service.move_task(task_id, section=section, sub=sub)
                    self._send_json(_build_payload(service))
                    return

                # /api/sections  → create a new, empty top-level section
                # (the panel's "+ Section" button, and Enter on a section
                # header). Body: {"section": "Name"} or, if a subsection
                # name is also given, {"section": "Name", "sub": "Sub"}
                # creates both in one call.
                if parsed.path == "/api/sections":
                    section = (body.get("section") or "").strip()
                    sub = (body.get("sub") or "").strip() or None
                    if not section:
                        self._send_json({"error": "section name is required"}, status=400)
                        return
                    if sub:
                        created = service.add_subsection(section, sub)
                    else:
                        created = service.add_section(section)
                    payload = _build_payload(service)
                    payload["created"] = created
                    self._send_json(payload)
                    return

                # /api/sections/rename  → rename a section (and, optionally
                # in the same call, scope it to renaming one subsection
                # within it instead). Body: {"old": "Work", "new": "Career"}
                # or {"section": "Work", "old_sub": "Reports", "new_sub": "Docs"}
                if parsed.path == "/api/sections/rename":
                    if "old_sub" in body or "new_sub" in body:
                        section = (body.get("section") or "").strip()
                        old_sub = (body.get("old_sub") or "").strip()
                        new_sub = (body.get("new_sub") or "").strip()
                        if not section or not old_sub or not new_sub:
                            self._send_json({"error": "section, old_sub, and new_sub are required"}, status=400)
                            return
                        renamed = service.rename_subsection(section, old_sub, new_sub)
                    else:
                        old_name = (body.get("old") or "").strip()
                        new_name = (body.get("new") or "").strip()
                        if not old_name or not new_name:
                            self._send_json({"error": "old and new names are required"}, status=400)
                            return
                        renamed = service.rename_section(old_name, new_name)
                    payload = _build_payload(service)
                    payload["renamed"] = renamed
                    self._send_json(payload)
                    return

                # ── Bulk operations (toolbar actions) ──────────────────────
                if parsed.path == "/api/bulk/rm_done":
                    removed = service.remove_done()
                    payload = _build_payload(service)
                    payload["removed_count"] = removed
                    self._send_json(payload)
                    return

                if parsed.path == "/api/bulk/archive":
                    archived = service.archive_done()
                    payload = _build_payload(service)
                    payload["archived_count"] = archived
                    self._send_json(payload)
                    return

                if parsed.path == "/api/bulk/clear":
                    # Confirmation happens in the browser UI (there's no TTY
                    # prompt to fall back to here) — the panel must show its
                    # own confirm dialog before calling this endpoint.
                    if not body.get("confirm"):
                        self._send_json({"error": "confirmation required"}, status=400)
                        return
                    service.clear_all()
                    self._send_json(_build_payload(service))
                    return

                self._send_json({"error": "not found"}, status=404)

            except TaskNotFoundError as e:
                self._send_json({"error": str(e)}, status=404)
            except TaskMDError as e:
                self._send_json({"error": str(e)}, status=400)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        def do_DELETE(self):
            from taskmd.exceptions import TaskNotFoundError
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            try:
                if len(parts) == 3 and parts[0] == "api" and parts[1] == "tasks":
                    task_id = parts[2]
                    service.remove_task(task_id)
                    self._send_json(_build_payload(service))
                    return
                self._send_json({"error": "not found"}, status=404)
            except TaskNotFoundError as e:
                self._send_json({"error": str(e)}, status=404)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

    return PanelHandler


def run_web_panel(service, port: Optional[int] = None, open_browser: bool = True, quiet: bool = False):
    """Start the TaskMD web control panel and block until Ctrl+C.

    Args:
        service: A TaskService bound to the user's live task file.
        port: Port to bind to. Auto-selects a free port near 7177 if omitted.
        open_browser: Whether to auto-open the default browser.
        quiet: If True, suppress the startup banner (used in tests).
    """
    from taskmd.ui.webpanel_assets import PANEL_HTML

    chosen_port = port or _find_free_port()
    handler_cls = make_handler(service, PANEL_HTML)
    httpd = ThreadingHTTPServer(("127.0.0.1", chosen_port), handler_cls)
    url = f"http://127.0.0.1:{chosen_port}/"

    if not quiet:
        print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
        print("\033[1m  🖥  TaskMD Control Panel\033[0m")
        print("\033[96m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
        print(f"  \033[92mRunning at:\033[0m {url}")
        print(f"  \033[90mWatching:\033[0m  {service.repo.file_path}")
        print("  \033[90mPress Ctrl+C to stop.\033[0m\n")

    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        if not quiet:
            print("\n\033[90mControl panel closed.\033[0m")


def start_web_panel_background(service, port: Optional[int] = None):
    """Start the panel server in a background thread; returns (httpd, thread, url).

    Useful for tests that need to make requests without blocking the test
    process forever in serve_forever().
    """
    from taskmd.ui.webpanel_assets import PANEL_HTML

    chosen_port = port or _find_free_port()
    handler_cls = make_handler(service, PANEL_HTML)
    httpd = ThreadingHTTPServer(("127.0.0.1", chosen_port), handler_cls)
    url = f"http://127.0.0.1:{chosen_port}/"

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread, url
