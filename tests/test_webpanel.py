"""
Tests for the TaskMD web control panel (TODOs.md Issue 4):
  "dashboard -live 应该可以调出一个控制面板，有UI界面的而不是仅仅CLI"
  ("dashboard --live should bring up a control panel with a real UI, not
  just CLI text") and "dashboard 改为 dashboard cli" (rename the bare
  `dashboard` command to `dashboard cli`).

Covers:
  - _build_payload() JSON serialization shape
  - HTTP routes: GET /, GET /api/state, POST status/field/add, DELETE
  - Round-trip correctness against the real markdown file
  - CLI wiring: `tm dashboard`, `tm dashboard cli`, `tm dashboard web`,
    `tm dashboard --live` all dispatch correctly
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest

from taskmd.repository import TaskRepository
from taskmd.service import TaskService
from taskmd.ui.webpanel import _build_payload, start_web_panel_background
from taskmd.ui.webpanel_assets import PANEL_HTML


SAMPLE_MD = """<!-- taskmd:version=2 -->

# Work
## Reports
- [ ] Write report <!-- id:t_01, due:2026-06-25, pri:3, tags:work -->
- [x] Submit invoice <!-- id:t_02 -->

## Meetings
- [-] Prepare slides <!-- id:t_03 -->

# Life
## Errands
- [ ] Buy milk <!-- id:t_04, tags:home -->
"""


@pytest.fixture
def panel_service(tmp_path):
    f = tmp_path / "tasks.md"
    f.write_text(SAMPLE_MD, encoding="utf-8")
    repo = TaskRepository(f)
    return TaskService(repo)


@pytest.fixture
def panel_server(panel_service):
    httpd, thread, url = start_web_panel_background(panel_service)
    time.sleep(0.2)
    yield url
    httpd.shutdown()


def http_get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.read()


def http_json(url, body=None, method="POST"):
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ─── Payload serialization ──────────────────────────────────────────────────

class TestBuildPayload:
    def test_payload_shape(self, panel_service):
        payload = _build_payload(panel_service)
        assert "tasks" in payload
        assert "sections" in payload
        assert "stats" in payload
        assert "task_file" in payload

    def test_payload_includes_all_tasks(self, panel_service):
        payload = _build_payload(panel_service)
        assert len(payload["tasks"]) == 4

    def test_payload_short_id_present(self, panel_service):
        payload = _build_payload(panel_service)
        t01 = next(t for t in payload["tasks"] if t["id"] == "t_01")
        assert t01["short_id"] == "01"

    def test_payload_sections_grouped(self, panel_service):
        payload = _build_payload(panel_service)
        assert "Work" in payload["sections"]
        assert "Life" in payload["sections"]
        assert "Reports" in payload["sections"]["Work"]
        assert "Meetings" in payload["sections"]["Work"]

    def test_payload_urgency_present(self, panel_service):
        payload = _build_payload(panel_service)
        t01 = next(t for t in payload["tasks"] if t["id"] == "t_01")
        assert "urgency" in t01

    def test_payload_stats_keys(self, panel_service):
        payload = _build_payload(panel_service)
        for key in ("total", "done", "in_progress", "todo", "overdue", "due_today", "completion_rate"):
            assert key in payload["stats"]


# ─── HTTP routes ─────────────────────────────────────────────────────────────

class TestPanelHTTPRoutes:
    def test_index_serves_html(self, panel_server):
        status, body = http_get(panel_server)
        assert status == 200
        assert b"TaskMD" in body

    def test_api_state_returns_json(self, panel_server):
        status, body = http_get(panel_server + "api/state")
        assert status == 200
        data = json.loads(body)
        assert len(data["tasks"]) == 4

    def test_unknown_route_404(self, panel_server):
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            http_get(panel_server + "api/nonexistent")
        assert exc_info.value.code == 404

    def test_post_status_change(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_01/status", {"status": "[x]"})
        assert status == 200
        t01 = next(t for t in data["tasks"] if t["id"] == "t_01")
        assert t01["status"] == "[x]"

    def test_post_status_invalid_value_rejected(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_01/status", {"status": "bogus"})
        assert status == 400

    def test_post_status_unknown_task_404(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_99/status", {"status": "[x]"})
        assert status == 404

    def test_post_field_due(self, panel_server):
        status, data = http_json(
            panel_server + "api/tasks/t_04/field", {"field": "due", "value": "2026-07-01 14:30"}
        )
        assert status == 200
        t04 = next(t for t in data["tasks"] if t["id"] == "t_04")
        assert t04["due"] == "2026-07-01 14:30"

    def test_post_field_disallowed_field_rejected(self, panel_server):
        status, data = http_json(
            panel_server + "api/tasks/t_04/field", {"field": "status", "value": "[x]"}
        )
        assert status == 400

    def test_post_add_task(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "New panel task"})
        assert status == 200
        names = [t["name"] for t in data["tasks"]]
        assert "New panel task" in names
        assert len(data["tasks"]) == 5

    def test_post_add_task_requires_name(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "   "})
        assert status == 400

    def test_delete_task(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_03", method="DELETE")
        assert status == 200
        ids = [t["id"] for t in data["tasks"]]
        assert "t_03" not in ids
        assert len(data["tasks"]) == 3

    def test_delete_unknown_task_404(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_99", method="DELETE")
        assert status == 404


# ─── Round-trip persistence ──────────────────────────────────────────────────

class TestPanelPersistence:
    def test_status_change_persists_to_file(self, panel_service, panel_server):
        http_json(panel_server + "api/tasks/t_02", method="DELETE")
        content = panel_service.repo.file_path.read_text(encoding="utf-8")
        assert "id:t_02" not in content

    def test_due_edit_persists_with_time_precision(self, panel_service, panel_server):
        http_json(panel_server + "api/tasks/t_01/field", {"field": "due", "value": "2026-09-01 08:30"})
        content = panel_service.repo.file_path.read_text(encoding="utf-8")
        assert "2026-09-01 08:30" in content

    def test_added_task_persists_with_new_id(self, panel_service, panel_server):
        http_json(panel_server + "api/tasks", {"name": "Persisted task"})
        content = panel_service.repo.file_path.read_text(encoding="utf-8")
        assert "Persisted task" in content
        assert "id:t_05" in content


# ─── Frontend asset sanity ───────────────────────────────────────────────────

class TestPanelHTML:
    def test_html_is_nonempty_and_well_formed(self):
        assert "<html" in PANEL_HTML
        assert "</html>" in PANEL_HTML
        assert "<script>" in PANEL_HTML

    def test_html_references_api_routes(self):
        assert "/api/state" in PANEL_HTML
        assert "/api/tasks" in PANEL_HTML

    def test_html_grid_has_six_columns_for_six_row_children(self):
        # Regression guard for the column/child-count mismatch bug found
        # during visual testing (priority stars wrapped onto their own line).
        assert "grid-template-columns: 22px 30px 1fr auto auto auto;" in PANEL_HTML


# ─── CLI integration ─────────────────────────────────────────────────────────

def run_tm(args, env_overrides, timeout=10):
    env = os.environ.copy()
    src_path = str(Path(__file__).parent.parent / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "taskmd.cli"] + args,
        capture_output=True, text=True, env=env, timeout=timeout,
    )


@pytest.fixture
def dash_env(tmp_path):
    task_file = tmp_path / "tasks.md"
    task_file.write_text(SAMPLE_MD, encoding="utf-8")
    return {"TASKMD_DB_PATH": str(task_file)}


class TestDashboardCLIDispatch:
    def test_bare_dashboard_renders_terminal_view(self, dash_env):
        result = run_tm(["dashboard"], dash_env)
        assert result.returncode == 0
        assert "Write report" in result.stdout or "01" in result.stdout

    def test_dashboard_cli_explicit_matches_bare(self, dash_env):
        bare = run_tm(["dashboard"], dash_env)
        explicit = run_tm(["dashboard", "cli"], dash_env)
        assert explicit.returncode == 0
        # Both should render the same kind of terminal output (not the web banner)
        assert "Control Panel" not in explicit.stdout

    def test_dashboard_cli_progress_flag(self, dash_env):
        result = run_tm(["dashboard", "cli", "--progress"], dash_env)
        assert result.returncode == 0
        assert "Progress" in result.stdout or "%" in result.stdout

    def test_dashboard_web_starts_server(self, dash_env):
        proc = subprocess.Popen(
            [sys.executable, "-m", "taskmd.cli", "dashboard", "web", "--no-browser", "--port", "7311"],
            env={**os.environ, **dash_env, "PYTHONPATH": str(Path(__file__).parent.parent / "src")},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            time.sleep(1.0)
            status, body = http_get("http://127.0.0.1:7311/api/state")
            assert status == 200
            data = json.loads(body)
            assert len(data["tasks"]) == 4
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_dashboard_live_flag_starts_server(self, dash_env):
        proc = subprocess.Popen(
            [sys.executable, "-m", "taskmd.cli", "dashboard", "--live", "--no-browser", "--port", "7312"],
            env={**os.environ, **dash_env, "PYTHONPATH": str(Path(__file__).parent.parent / "src")},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            time.sleep(1.0)
            status, body = http_get("http://127.0.0.1:7312/")
            assert status == 200
            assert b"TaskMD" in body
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_dashboard_listed_in_help_with_web_and_cli(self, dash_env):
        result = run_tm(["help"], dash_env)
        assert "dashboard cli" in result.stdout
        assert "dashboard web" in result.stdout
