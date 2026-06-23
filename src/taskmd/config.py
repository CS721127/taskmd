"""
Configuration loader for TaskMD Lite.

Priority chain (highest to lowest):
  1. CLI arguments (passed at runtime)
  2. Environment variables (TASKMD_*)
  3. Config file (~/.config/taskmd/config.toml)
  4. Defaults
"""
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from taskmd.paths import get_config_file, get_default_task_file


# Inline TOML reader that works on all Python 3.9+
def _load_toml(path: Path) -> dict:
    """Load a TOML file, using tomllib (3.11+) or tomli fallback."""
    try:
        import tomllib
    except ModuleNotFoundError:
        try:
            import tomli as tomllib
        except ModuleNotFoundError:
            return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _save_toml(path: Path, data: dict):
    """Save a dict as TOML."""
    try:
        import tomli_w
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
    except ImportError:
        # Fallback: write minimal TOML manually
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for k, v in data.items():
            if isinstance(v, bool):
                lines.append(f"{k} = {'true' if v else 'false'}")
            elif isinstance(v, str):
                lines.append(f'{k} = "{v}"')
            else:
                lines.append(f"{k} = {v}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass
class Config:
    """Resolved configuration for TaskMD Lite."""
    task_file: Path = None
    theme: str = "default"
    editor: str = "nano"
    timezone: str = "Australia/Sydney"
    auto_git_backup: bool = False
    default_view: str = "tree"
    archive_file: Path = None
    export_dir: Path = None

    def __post_init__(self):
        if self.task_file is None:
            self.task_file = get_default_task_file()
        if self.archive_file is None:
            from taskmd.paths import get_archive_file
            self.archive_file = get_archive_file()
        if self.export_dir is None:
            # Default: current working directory, matching legacy behaviour
            # (exports land next to wherever the user ran `tm` from).
            self.export_dir = Path.cwd()


# Default values used when nothing is configured
_DEFAULTS = {
    "db_path": None,  # Will resolve to get_default_task_file()
    "theme": "default",
    "editor": "nano",
    "timezone": "Australia/Sydney",
    "auto_git_backup": False,
    "default_view": "tree",
    "export_dir": None,  # Will resolve to Path.cwd()
}

# Mapping from env var names to config keys
_ENV_MAP = {
    "TASKMD_DB_PATH": "db_path",
    "TASKMD_THEME": "theme",
    "TASKMD_EDITOR": "editor",
    "TASKMD_TIMEZONE": "timezone",
    "TASKMD_EXPORT_DIR": "export_dir",
}


def load_config(cli_overrides: dict = None) -> Config:
    """Load config with full priority chain.

    Args:
        cli_overrides: Optional dict of overrides from CLI arguments.

    Returns:
        Resolved Config instance.
    """
    # Start with defaults
    merged = dict(_DEFAULTS)

    # Layer 3: Config file
    config_file = get_config_file()
    if config_file.exists():
        file_data = _load_toml(config_file)
        for k, v in file_data.items():
            if k in merged:
                merged[k] = v

    # Layer 2: Environment variables
    for env_key, config_key in _ENV_MAP.items():
        val = os.getenv(env_key)
        if val is not None:
            if config_key == "auto_git_backup":
                merged[config_key] = val.lower() in ("true", "1", "yes")
            else:
                merged[config_key] = val

    # Layer 1: CLI overrides
    if cli_overrides:
        for k, v in cli_overrides.items():
            if v is not None and k in merged:
                merged[k] = v

    # Resolve into Config object
    task_file = None
    if merged.get("db_path"):
        task_file = Path(os.path.expanduser(merged["db_path"]))

    export_dir = None
    if merged.get("export_dir"):
        export_dir = Path(os.path.expanduser(merged["export_dir"]))

    return Config(
        task_file=task_file,
        theme=merged["theme"],
        editor=merged["editor"],
        timezone=merged["timezone"],
        auto_git_backup=merged["auto_git_backup"],
        default_view=merged["default_view"],
        export_dir=export_dir,
    )


def get_config_summary() -> str:
    """Return a formatted string showing current config values and sources."""
    config = load_config()
    config_file = get_config_file()
    file_exists = config_file.exists()

    lines = [
        "\033[96m[CONFIG]\033[0m",
        f"  Task file     : {config.task_file}",
        f"  Config file   : {config_file} ({'exists' if file_exists else 'not created yet'})",
        f"  Theme         : {config.theme}",
        f"  Editor        : {config.editor}",
        f"  Timezone      : {config.timezone}",
        f"  Default view  : {config.default_view}",
        f"  Git backup    : {config.auto_git_backup}",
        f"  Export dir    : {config.export_dir}",
    ]
    return "\n".join(lines)


def init_default_config():
    """Create a default config file if it doesn't exist."""
    config_file = get_config_file()
    if not config_file.exists():
        default_data = {
            "db_path": str(get_default_task_file()),
            "theme": "default",
            "editor": os.getenv("EDITOR", "nano"),
            "timezone": "Australia/Sydney",
            "auto_git_backup": False,
            "default_view": "tree",
            "export_dir": str(Path.cwd()),
        }
        _save_toml(config_file, default_data)
        return True
    return False
