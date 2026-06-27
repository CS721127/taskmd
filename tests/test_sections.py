"""
Tests for section/subsection creation, renaming, and listing — added to
support the web control panel's "+ Section" / "+ Subsection" / "+ Task"
buttons and Enter-to-create-sibling keyboard behavior.

Covers:
  - TaskService.add_section / add_subsection / rename_section /
    rename_subsection / get_all_sections
  - Correct blank-line placement so newly created subsections are visually
    grouped under the right section (regression guard for a bug found
    during implementation)
  - Empty sections/subsections surviving a parse-write round trip
  - Web panel routes: POST /api/sections, POST /api/sections/rename
  - _build_payload seeding empty sections/subs from the document, not just
    from existing tasks (regression guard — an empty section created via
    add_section was initially invisible in the panel payload)
"""
import json
import time
import urllib.request
import urllib.error

import pytest

from taskmd.repository import TaskRepository
from taskmd.service import TaskService
from taskmd.exceptions import ValidationError


# ─── TaskService.add_section / add_subsection ──────────────────────────────

class TestAddSection:
    def test_creates_new_section(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- [ ] Task <!-- id:t_01 -->\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        created = service.add_section("Personal")
        assert created is True
        content = f.read_text(encoding="utf-8")
        assert "# Personal" in content

    def test_no_op_if_section_already_exists(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        assert service.add_section("Work") is False

    def test_empty_name_raises(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        with pytest.raises(ValidationError):
            service.add_section("")

    def test_works_on_completely_empty_file(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        assert service.add_section("Inbox") is True
        assert "# Inbox" in f.read_text(encoding="utf-8")

    def test_new_section_survives_reparse_with_no_tasks(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        service.add_section("Personal")
        service2 = TaskService(TaskRepository(f))
        sections = service2.get_all_sections()
        assert "Personal" in sections
        assert sections["Personal"] == []


class TestAddSubsection:
    def test_creates_subsection_under_existing_section(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- [ ] Task <!-- id:t_01 -->\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        created = service.add_subsection("Work", "Meetings")
        assert created is True
        content = f.read_text(encoding="utf-8")
        assert "## Meetings" in content

    def test_new_subsection_grouped_under_correct_section_not_next_one(self, tmp_path):
        """Regression guard: a new subsection must land right after the
        section's existing content, not after the blank-line separator that
        visually belongs to the *next* section."""
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- [ ] Task <!-- id:t_01 -->\n\n# Personal\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        service.add_subsection("Work", "Meetings")
        content = f.read_text(encoding="utf-8")
        lines = content.splitlines()
        meetings_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Meetings")
        personal_idx = next(i for i, l in enumerate(lines) if l.strip() == "# Personal")
        assert meetings_idx < personal_idx
        assert lines[personal_idx - 1].strip() == ""

    def test_creates_section_too_if_it_does_not_exist(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        created = service.add_subsection("Health", "Checkups")
        assert created is True
        content = f.read_text(encoding="utf-8")
        assert "# Health" in content
        assert "## Checkups" in content

    def test_no_op_if_subsection_already_exists(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        assert service.add_subsection("Work", "Reports") is False

    def test_empty_names_raise(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        with pytest.raises(ValidationError):
            service.add_subsection("", "Sub")
        with pytest.raises(ValidationError):
            service.add_subsection("Work", "")

    def test_new_task_can_be_added_to_freshly_created_subsection(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        service.add_subsection("Work", "Meetings")
        service.add_task(name="Standup", section="Work", sub="Meetings")
        tasks = service.get_all_tasks()
        assert any(t.name == "Standup" and t.sub == "Meetings" for t in tasks)


class TestGetAllSections:
    def test_includes_sections_with_tasks(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- [ ] Task <!-- id:t_01 -->\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        sections = service.get_all_sections()
        assert sections == {"Work": ["Reports"]}

    def test_includes_empty_sections_and_subsections(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n\n# Personal\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        sections = service.get_all_sections()
        assert sections == {"Work": ["Reports"], "Personal": []}

    def test_preserves_document_order(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Zebra\n## A\n# Apple\n## B\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        sections = service.get_all_sections()
        assert list(sections.keys()) == ["Zebra", "Apple"]


# ─── rename_section / rename_subsection ─────────────────────────────────────

class TestRenameSection:
    def test_renames_header_and_tasks(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n"
            "- [ ] Task A <!-- id:t_01 -->\n- [ ] Task B <!-- id:t_02 -->\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        assert service.rename_section("Work", "Career") is True
        content = f.read_text(encoding="utf-8")
        assert "# Career" in content
        assert "# Work" not in content
        tasks = service.get_all_tasks()
        assert all(t.section == "Career" for t in tasks)

    def test_no_op_for_nonexistent_section(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        assert service.rename_section("DoesNotExist", "X") is False

    def test_no_op_for_same_name(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        assert service.rename_section("Work", "Work") is False

    def test_raises_if_new_name_already_exists(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n# Personal\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        with pytest.raises(ValidationError):
            service.rename_section("Work", "Personal")


class TestRenameSubsection:
    def test_renames_header_and_tasks(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text(
            "<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- [ ] Task A <!-- id:t_01 -->\n",
            encoding="utf-8",
        )
        service = TaskService(TaskRepository(f))
        assert service.rename_subsection("Work", "Reports", "Documents") is True
        content = f.read_text(encoding="utf-8")
        assert "## Documents" in content
        tasks = service.get_all_tasks()
        assert tasks[0].sub == "Documents"

    def test_raises_if_new_sub_name_already_exists(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n## Meetings\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        with pytest.raises(ValidationError):
            service.rename_subsection("Work", "Reports", "Meetings")

    def test_no_op_for_nonexistent_subsection(self, tmp_path):
        f = tmp_path / "tasks.md"
        f.write_text("<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n", encoding="utf-8")
        service = TaskService(TaskRepository(f))
        assert service.rename_subsection("Work", "DoesNotExist", "X") is False


# ─── Web panel API routes ────────────────────────────────────────────────────

def http_json(url, body=None, method="POST"):
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


@pytest.fixture
def section_service(tmp_path):
    f = tmp_path / "tasks.md"
    f.write_text(
        "<!-- taskmd:version=2 -->\n\n# Work\n## Reports\n- [ ] Task A <!-- id:t_01 -->\n",
        encoding="utf-8",
    )
    return TaskService(TaskRepository(f))


@pytest.fixture
def section_server(section_service):
    from taskmd.ui.webpanel import start_web_panel_background
    httpd, thread, url = start_web_panel_background(section_service)
    time.sleep(0.2)
    yield url
    httpd.shutdown()


class TestSectionsAPIRoute:
    def test_create_section(self, section_server):
        status, data = http_json(section_server + "api/sections", {"section": "Personal"})
        assert status == 200
        assert data["created"] is True
        assert "Personal" in data["sections"]

    def test_create_section_with_subsection(self, section_server):
        status, data = http_json(section_server + "api/sections", {"section": "Personal", "sub": "Errands"})
        assert status == 200
        assert "Errands" in data["sections"]["Personal"]

    def test_create_subsection_under_existing_section(self, section_server):
        status, data = http_json(section_server + "api/sections", {"section": "Work", "sub": "Meetings"})
        assert status == 200
        assert "Meetings" in data["sections"]["Work"]
        assert "Reports" in data["sections"]["Work"]

    def test_empty_section_name_rejected(self, section_server):
        status, data = http_json(section_server + "api/sections", {"section": ""})
        assert status == 400

    def test_new_empty_section_visible_in_payload(self, section_server):
        status, data = http_json(section_server + "api/sections", {"section": "Empty"})
        assert data["sections"]["Empty"] == {}


class TestSectionsRenameAPIRoute:
    def test_rename_section(self, section_server):
        status, data = http_json(section_server + "api/sections/rename", {"old": "Work", "new": "Career"})
        assert status == 200
        assert data["renamed"] is True
        assert "Career" in data["sections"]
        assert "Work" not in data["sections"]

    def test_rename_subsection(self, section_server):
        status, data = http_json(
            section_server + "api/sections/rename",
            {"section": "Work", "old_sub": "Reports", "new_sub": "Docs"},
        )
        assert status == 200
        assert data["renamed"] is True
        assert "Docs" in data["sections"]["Work"]

    def test_rename_missing_fields_rejected(self, section_server):
        status, data = http_json(section_server + "api/sections/rename", {"old": "Work"})
        assert status == 400

    def test_rename_persists_to_file(self, section_service, section_server):
        http_json(section_server + "api/sections/rename", {"old": "Work", "new": "Career"})
        content = section_service.repo.file_path.read_text(encoding="utf-8")
        assert "# Career" in content
