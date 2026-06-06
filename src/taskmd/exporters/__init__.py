"""
TaskMD Exporters package.

  csv    — Standard spreadsheet (stdlib only)
  json   — Structured JSON (stdlib only)
  html   — Single-file HTML kanban board (stdlib only)
  svg    — Static SVG kanban image (stdlib only)
  report — Markdown weekly/daily reports (stdlib only)
  ics    — iCalendar  (requires: pip install 'taskmd[export]')
  pdf    — PDF report (requires: pip install 'taskmd[export]')
  png    — PNG image  (requires: pip install 'taskmd[export]')
"""
from taskmd.exporters.csv_exporter import export_csv
from taskmd.exporters.json_exporter import export_json
from taskmd.exporters.html_exporter import export_html
from taskmd.exporters.image_exporter import export_svg
from taskmd.exporters.report import generate_weekly_report, generate_daily_report

__all__ = [
    "export_csv",
    "export_json",
    "export_html",
    "export_svg",
    "generate_weekly_report",
    "generate_daily_report",
    "export_ics",
    "export_pdf",
    "export_png",
]


def export_ics(tasks, output_path=None, only_pending=False, calendar_name="TaskMD"):
    """Export to iCalendar. Requires: pip install 'taskmd[export]'"""
    from taskmd.exporters.ics_exporter import export_ics as _f
    return _f(tasks, output_path=output_path, only_pending=only_pending,
               calendar_name=calendar_name)


def export_pdf(tasks, output_path=None, month=None, theme="light", only_pending=False):
    """Export to PDF. Requires: pip install 'taskmd[export]'"""
    from taskmd.exporters.pdf_exporter import export_pdf as _f
    return _f(tasks, output_path=output_path, month=month,
              theme=theme, only_pending=only_pending)


def export_png(tasks, output_path=None, theme="light", scale=2.0):
    """Export to PNG. Requires: pip install 'taskmd[export]'"""
    from taskmd.exporters.image_exporter import export_png as _f
    return _f(tasks, output_path=output_path, theme=theme, scale=scale)
