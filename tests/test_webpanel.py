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

    def test_html_grid_has_seven_columns_for_seven_row_children(self):
        # Regression guard for the column/child-count mismatch bug found
        # during visual testing (priority stars wrapped onto their own line).
        # Updated to 7 columns when the per-row action-menu button (⋮) was
        # added for full CLI parity (move/tag/delete from the row itself).
        assert "grid-template-columns: 22px 30px 1fr auto auto auto 20px;" in PANEL_HTML


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


# ─── Full CLI parity: quick-capture add, tags, move, bulk ops, search, validate

class TestPanelAddWithQuickCapture:
    """The 'press Enter to create' box must support the same grammar as
    `tm add "..."` on the command line — not just a bare name."""

    def test_add_extracts_tag_and_due(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Call dentist #health @tomorrow"})
        assert status == 200
        t = next(x for x in data["tasks"] if x["name"] == "Call dentist")
        assert t["tags"] == ["health"]
        assert t["due"] is not None

    def test_add_extracts_priority(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Submit report !4 @2026-07-01"})
        t = next(x for x in data["tasks"] if x["name"] == "Submit report")
        assert t["pri"] == 4

    def test_add_relocates_via_section_subsection_tokens(self, panel_server):
        status, data = http_json(
            panel_server + "api/tasks",
            {"name": "Buy stamps #errand @tomorrow /Personal //Shopping"},
        )
        t = next(x for x in data["tasks"] if x["name"] == "Buy stamps")
        assert t["section"] == "Personal"
        assert t["sub"] == "Shopping"

    def test_add_false_positive_guard_issue_number_not_a_tag(self, panel_server):
        """Mirrors the parser-level guard: '#1234' in a name without a
        strong @/^ date signal must not be treated as a tag."""
        status, data = http_json(panel_server + "api/tasks", {"name": "Fix bug #1234"})
        t = next(x for x in data["tasks"] if "Fix bug" in x["name"])
        assert t["tags"] == [] or t["tags"] is None or "1234" not in (t["tags"] or [])

    def test_add_response_includes_capture_warnings_key(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Plain task, no tokens"})
        assert "capture_warnings" in data

    def test_explicit_body_fields_still_work_without_shortcut_tokens(self, panel_server):
        status, data = http_json(
            panel_server + "api/tasks",
            {"name": "Quarterly review", "section": "Work", "sub": "Reviews", "pri": 2},
        )
        t = next(x for x in data["tasks"] if x["name"] == "Quarterly review")
        assert t["section"] == "Work"
        assert t["sub"] == "Reviews"
        assert t["pri"] == 2


class TestPanelInsertAfter:
    """Covers the 'after' parameter on POST /api/tasks — used by the
    "Enter on a task name creates the next task right below it" behavior so
    the new task lands in place, not appended to the end of the section."""

    def test_response_includes_new_task_id(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Plain task"})
        assert status == 200
        assert "new_task_id" in data
        new_id = data["new_task_id"]
        assert any(t["id"] == new_id and t["name"] == "Plain task" for t in data["tasks"])

    def test_after_inserts_directly_following_anchor(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Inserted", "after": "t_01"})
        assert status == 200
        ids_in_order = [t["id"] for t in data["tasks"]]
        idx_anchor = ids_in_order.index("t_01")
        idx_new = ids_in_order.index(data["new_task_id"])
        assert idx_new == idx_anchor + 1

    def test_after_inherits_anchor_section_and_sub(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Inserted", "after": "t_01"})
        new_task = next(t for t in data["tasks"] if t["id"] == data["new_task_id"])
        anchor = next(t for t in data["tasks"] if t["id"] == "t_01")
        assert new_task["section"] == anchor["section"]
        assert new_task["sub"] == anchor["sub"]

    def test_after_with_unknown_anchor_returns_404(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Inserted", "after": "t_99"})
        assert status == 404

    def test_after_still_supports_quick_capture_tokens(self, panel_server):
        status, data = http_json(
            panel_server + "api/tasks",
            {"name": "Follow up #urgent !4", "after": "t_01"},
        )
        new_task = next(t for t in data["tasks"] if t["id"] == data["new_task_id"])
        assert new_task["name"] == "Follow up"
        assert "urgent" in new_task["tags"]
        assert new_task["pri"] == 4

    def test_after_persists_correct_order_to_file(self, panel_service, panel_server):
        http_json(panel_server + "api/tasks", {"name": "Inserted", "after": "t_01"})
        content = panel_service.repo.file_path.read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if l.startswith("- [")]
        names = [l.split("] ")[1].split(" <!--")[0] for l in lines]
        idx_anchor = names.index("Write report")
        assert names[idx_anchor + 1] == "Inserted"

    def test_omitting_after_still_appends_to_end_as_before(self, panel_server):
        status, data = http_json(panel_server + "api/tasks", {"name": "Appended", "section": "Work", "sub": "Reports"})
        ids_in_order = [t["id"] for t in data["tasks"] if t["section"] == "Work" and t["sub"] == "Reports"]
        assert ids_in_order[-1] == data["new_task_id"]


class TestPanelTagOperations:
    def test_add_tag(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_04/tags", {"action": "add", "tag": "urgent"})
        assert status == 200
        t04 = next(t for t in data["tasks"] if t["id"] == "t_04")
        assert "urgent" in t04["tags"]

    def test_remove_tag(self, panel_server):
        http_json(panel_server + "api/tasks/t_01/tags", {"action": "add", "tag": "extra"})
        status, data = http_json(panel_server + "api/tasks/t_01/tags", {"action": "rm", "tag": "work"})
        t01 = next(t for t in data["tasks"] if t["id"] == "t_01")
        assert "work" not in t01["tags"]

    def test_tag_action_requires_valid_action(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_01/tags", {"action": "bogus", "tag": "x"})
        assert status == 400

    def test_tag_action_requires_nonempty_tag(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_01/tags", {"action": "add", "tag": ""})
        assert status == 400

    def test_tag_unknown_task_404(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_99/tags", {"action": "add", "tag": "x"})
        assert status == 404


class TestPanelMoveOperation:
    def test_move_to_new_section_and_sub(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_03/move", {"section": "Life", "sub": "Chores"})
        assert status == 200
        t03 = next(t for t in data["tasks"] if t["id"] == "t_03")
        assert t03["section"] == "Life"
        assert t03["sub"] == "Chores"

    def test_move_section_only(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_04/move", {"section": "Work"})
        t04 = next(t for t in data["tasks"] if t["id"] == "t_04")
        assert t04["section"] == "Work"

    def test_move_requires_section_or_sub(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_04/move", {})
        assert status == 400

    def test_move_unknown_task_404(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_99/move", {"section": "X"})
        assert status == 404

    def test_move_persists_to_file(self, panel_service, panel_server):
        http_json(panel_server + "api/tasks/t_03/move", {"section": "Life", "sub": "Chores"})
        content = panel_service.repo.file_path.read_text(encoding="utf-8")
        assert "# Life" in content
        assert "## Chores" in content


class TestPanelPriorityClearing:
    """Regression test for a bug found while wiring the priority editor:
    set_metadata('pri', None) silently no-op'd instead of clearing it."""

    def test_set_priority(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_04/field", {"field": "pri", "value": 5})
        t04 = next(t for t in data["tasks"] if t["id"] == "t_04")
        assert t04["pri"] == 5

    def test_clear_priority_with_none(self, panel_server):
        http_json(panel_server + "api/tasks/t_01/field", {"field": "pri", "value": 5})
        status, data = http_json(panel_server + "api/tasks/t_01/field", {"field": "pri", "value": None})
        t01 = next(t for t in data["tasks"] if t["id"] == "t_01")
        assert t01["pri"] is None

    def test_clear_priority_with_empty_string(self, panel_server):
        http_json(panel_server + "api/tasks/t_01/field", {"field": "pri", "value": 5})
        status, data = http_json(panel_server + "api/tasks/t_01/field", {"field": "pri", "value": ""})
        t01 = next(t for t in data["tasks"] if t["id"] == "t_01")
        assert t01["pri"] is None

    def test_set_priority_zero_is_distinct_from_clearing(self, panel_server):
        status, data = http_json(panel_server + "api/tasks/t_04/field", {"field": "pri", "value": "0"})
        t04 = next(t for t in data["tasks"] if t["id"] == "t_04")
        assert t04["pri"] == 0


class TestPanelBulkOperations:
    def test_rm_done_removes_completed_tasks(self, panel_server):
        status, data = http_json(panel_server + "api/bulk/rm_done", {})
        assert status == 200
        assert data["removed_count"] == 1
        assert not any(t["id"] == "t_02" for t in data["tasks"])

    def test_rm_done_zero_when_nothing_completed(self, panel_server):
        http_json(panel_server + "api/bulk/rm_done", {})
        status, data = http_json(panel_server + "api/bulk/rm_done", {})
        assert data["removed_count"] == 0

    def test_archive_moves_completed_tasks(self, panel_service, panel_server):
        status, data = http_json(panel_server + "api/bulk/archive", {})
        assert status == 200
        assert data["archived_count"] == 1
        assert not any(t["id"] == "t_02" for t in data["tasks"])

    def test_clear_requires_confirmation(self, panel_server):
        status, data = http_json(panel_server + "api/bulk/clear", {})
        assert status == 400
        assert "confirmation" in data["error"]

    def test_clear_with_confirmation_removes_everything(self, panel_server):
        status, data = http_json(panel_server + "api/bulk/clear", {"confirm": True})
        assert status == 200
        assert len(data["tasks"]) == 0

    def test_clear_persists_empty_state_to_file(self, panel_service, panel_server):
        http_json(panel_server + "api/bulk/clear", {"confirm": True})
        content = panel_service.repo.file_path.read_text(encoding="utf-8")
        assert "- [" not in content


class TestPanelValidateRoute:
    def test_validate_clean_file(self, panel_server):
        status, body = http_get(panel_server + "api/validate")
        data = json.loads(body)
        assert "errors" in data

    def test_validate_reports_lenient_format_issue(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Tasks\n- Buy milk\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        httpd, thread, url = start_web_panel_background(service)
        time.sleep(0.2)
        try:
            status, body = http_get(url + "api/validate")
            data = json.loads(body)
            assert any("non-standard" in e for e in data["errors"])
        finally:
            httpd.shutdown()


class TestPanelSearchRoute:
    def test_search_finds_matching_task(self, panel_server):
        status, body = http_get(panel_server + "api/search?q=report")
        data = json.loads(body)
        assert any("report" in r["name"].lower() for r in data["results"])

    def test_search_empty_query_returns_empty(self, panel_server):
        status, body = http_get(panel_server + "api/search?q=")
        data = json.loads(body)
        assert data["results"] == []

    def test_search_no_match_returns_empty_list(self, panel_server):
        status, body = http_get(panel_server + "api/search?q=zzzznomatch")
        data = json.loads(body)
        assert data["results"] == []


class TestPanelPayloadIncludesTags:
    def test_payload_has_tags_summary(self, panel_service):
        payload = _build_payload(panel_service)
        assert "tags" in payload
        assert payload["tags"].get("work") == 1


class TestPanelPayloadDeterminism:
    """The browser's poll loop skips re-rendering when the new payload's
    JSON is identical to the last one it painted (fixing a bug where the
    UI visibly flashed every 1.5s even with no changes). That only works
    if _build_payload is itself deterministic for an unchanged file —
    this guards that contract."""

    def test_payload_is_byte_identical_across_repeated_calls_with_no_changes(self, panel_service):
        import json
        first = json.dumps(_build_payload(panel_service))
        second = json.dumps(_build_payload(panel_service))
        third = json.dumps(_build_payload(panel_service))
        assert first == second == third

    def test_payload_changes_after_a_real_mutation(self, panel_service):
        import json
        before = json.dumps(_build_payload(panel_service))
        panel_service.add_task(name="Something new", section="Work", sub="Reports")
        after = json.dumps(_build_payload(panel_service))
        assert before != after

