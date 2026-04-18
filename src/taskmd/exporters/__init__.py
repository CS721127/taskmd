"""
TaskMD Exporters package.

Provides export capabilities for tasks:
  - CSV: Standard spreadsheet format
  - JSON: Structured data format
  - ICS: iCalendar format (requires: pip install 'taskmd[export]')
  - HTML: Single-file kanban board
  - Report: Markdown weekly/daily reports
"""
from taskmd.exporters.csv_exporter import export_csv
from taskmd.exporters.json_exporter import export_json
from taskmd.exporters.html_exporter import export_html
from taskmd.exporters.report import generate_weekly_report, generate_daily_report

__all__ = [
    "export_csv",
    "export_json",
    "export_html",
    "generate_weekly_report",
    "generate_daily_report",
    "export_ics",
]


def export_ics(tasks, output_path=None, only_pending=False, calendar_name="TaskMD"):
    """Export tasks to ICS format. Requires: pip install 'taskmd[export]'"""
    from taskmd.exporters.ics_exporter import export_ics as _export_ics
    return _export_ics(
        tasks,
        output_path=output_path,
        only_pending=only_pending,
        calendar_name=calendar_name,
    )
