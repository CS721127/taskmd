"""
Tests for source-file export and configurable export directory
(TODOs.md Issue 7):
  - markdown_to_plain_text conversion
  - export_source (.md copy and .txt conversion)
  - Config.export_dir resolution
  - CLI: `tm export source|md|txt`, --output with directory, export_dir config
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from taskmd.exporters.source_exporter import markdown_to_plain_text, export_source


SAMPLE_MD = """<!-- taskmd:version=2 -->
<!-- taskmd:timezone=Australia/Sydney -->

# Work
## Reports
- [ ] Write report <!-- id:t_01, due:2026-06-25, pri:3 -->
- [x] Submit invoice <!-- id:t_02, done:2026-06-20T10:00:00 -->

## Meetings
- [-] Prepare slides <!-- id:t_03 -->

# Life
## Errands
- [ ] Buy milk <!-- id:t_04, tags:home -->
"""


class TestMarkdownToPlainText:
    def test_drops_config_comments(self):
        result = markdown_to_plain_text(SAMPLE_MD)
        assert "taskmd:version" not in result
        assert "taskmd:timezone" not in result

    def test_section_headers_uppercased(self):
        result = markdown_to_plain_text(SAMPLE_MD)
        assert "WORK" in result
        assert "LIFE" in result

    def test_subsection_headers_indented(self):
        result = markdown_to_plain_text(SAMPLE_MD)
        assert "Reports:" in result
        assert "Errands:" in result

    def test_status_labels_replace_checkboxes(self):
        result = markdown_to_plain_text(SAMPLE_MD)
        assert "[TODO] Write report" in result
        assert "[DONE] Submit invoice" in result
        assert "[IN PROGRESS] Prepare slides" in result

    def test_hidden_metadata_stripped_from_task_lines(self):
        result = markdown_to_plain_text(SAMPLE_MD)
        assert "id:t_01" not in result
        assert "<!--" not in result

    def test_no_excessive_blank_lines(self):
        result = markdown_to_plain_text(SAMPLE_MD)
        assert "\n\n\n" not in result


class TestExportSource:
    def test_export_md_copies_verbatim(self, tmp_path):
        src = tmp_path / "tasks.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "out" / "copy.md"
        content = export_source(src, out, as_txt=False)
        assert out.exists()
        assert content == SAMPLE_MD
        assert out.read_text(encoding="utf-8") == SAMPLE_MD

    def test_export_txt_converts(self, tmp_path):
        src = tmp_path / "tasks.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "out" / "copy.txt"
        content = export_source(src, out, as_txt=True)
        assert out.exists()
        assert "[TODO]" in content
        assert "<!--" not in content

    def test_missing_source_raises(self, tmp_path):
        src = tmp_path / "doesnotexist.md"
        out = tmp_path / "copy.md"
        with pytest.raises(FileNotFoundError):
            export_source(src, out, as_txt=False)

    def test_creates_output_directory(self, tmp_path):
        src = tmp_path / "tasks.md"
        src.write_text(SAMPLE_MD, encoding="utf-8")
        out = tmp_path / "deep" / "nested" / "dir" / "copy.md"
        export_source(src, out, as_txt=False)
        assert out.exists()


# ─── Config export_dir ──────────────────────────────────────────────────────

class TestConfigExportDir:
    def test_default_export_dir_is_cwd(self):
        from taskmd.config import Config
        cfg = Config()
        assert Path(cfg.export_dir) == Path.cwd()

    def test_explicit_export_dir_respected(self, tmp_path):
        from taskmd.config import Config
        cfg = Config(export_dir=tmp_path / "myexports")
        assert Path(cfg.export_dir) == tmp_path / "myexports"

    def test_env_var_overrides_export_dir(self, tmp_path, monkeypatch):
        from taskmd.config import load_config
        monkeypatch.setenv("TASKMD_EXPORT_DIR", str(tmp_path / "from_env"))
        cfg = load_config()
        assert Path(cfg.export_dir) == tmp_path / "from_env"


# ─── CLI integration ─────────────────────────────────────────────────────────

def run_tm(args, env_overrides, cwd=None):
    env = os.environ.copy()
    src_path = str(Path(__file__).parent.parent / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-m", "taskmd.cli"] + args,
        capture_output=True, text=True, env=env, timeout=10, cwd=cwd,
    )


@pytest.fixture
def source_env(tmp_path):
    task_file = tmp_path / "tasks.md"
    task_file.write_text(SAMPLE_MD, encoding="utf-8")
    return {"TASKMD_DB_PATH": str(task_file)}, tmp_path


class TestExportSourceCLI:
    def test_export_source_default_location(self, source_env):
        env, cwd = source_env
        result = run_tm(["export", "source"], env, cwd=str(cwd))
        assert result.returncode == 0
        assert (cwd / "tasks_source.md").exists()

    def test_export_txt_default_location(self, source_env):
        env, cwd = source_env
        result = run_tm(["export", "txt"], env, cwd=str(cwd))
        assert result.returncode == 0
        out_file = cwd / "tasks_source.txt"
        assert out_file.exists()
        text = out_file.read_text(encoding="utf-8")
        assert "[TODO]" in text or "[DONE]" in text

    def test_export_md_with_explicit_subdir(self, source_env):
        env, cwd = source_env
        result = run_tm(["export", "md", "--output", "backups/schedule.md"], env, cwd=str(cwd))
        assert result.returncode == 0
        assert (cwd / "backups" / "schedule.md").exists()

    def test_export_dir_env_redirects_bare_filename(self, source_env):
        env, cwd = source_env
        export_dir = cwd / "myexports"
        env = dict(env)
        env["TASKMD_EXPORT_DIR"] = str(export_dir)
        result = run_tm(["export", "csv"], env, cwd=str(cwd))
        assert result.returncode == 0
        assert (export_dir / "tasks_export.csv").exists()
        assert not (cwd / "tasks_export.csv").exists()
