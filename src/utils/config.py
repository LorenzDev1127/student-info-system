"""Configuration management.

Settings live in ``config/config.json``. Anything missing from that file falls
back to ``DEFAULTS``, so the app still runs if the file is deleted.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"

DEFAULTS: dict[str, Any] = {
    "app": {"name": "Student Information System", "version": "1.0.0"},
    "storage": {"data_file": "data/students.json", "backup_on_corrupt": True},
    "logging": {
        "level": "INFO",
        "file": "logs/app.log",
        "max_bytes": 1_048_576,
        "backup_count": 3,
        "console": False,
    },
    "export": {"directory": "exports"},
    "students": {
        "id_prefix": "STU",
        "min_year_level": 1,
        "max_year_level": 5,
        "min_gpa": 1.0,
        "max_gpa": 5.0,
    },
    "ui": {"use_colors": True, "clear_screen": True},
}


class ConfigError(Exception):
    """Raised when the configuration file exists but cannot be used."""


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively copy values from ``override`` into ``base``."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


class Config:
    """Read-only access to settings using dotted keys, e.g. ``"logging.level"``."""

    def __init__(self, data: dict[str, Any], root: Path = PROJECT_ROOT) -> None:
        self._data = data
        self.root = root

    def get(self, dotted_key: str, default: Any = None) -> Any:
        node: Any = self._data
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def path(self, dotted_key: str) -> Path:
        """Return a setting as a Path, resolved against the project root."""
        value = self.get(dotted_key)
        if value is None:
            raise ConfigError(f"Missing path setting: {dotted_key}")
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Load settings from ``path`` merged over the defaults."""
    data = deepcopy(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as file:
            user_settings = json.load(file)
    except FileNotFoundError:
        return Config(data)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path.name} is not valid JSON (line {exc.lineno}).") from exc

    if not isinstance(user_settings, dict):
        raise ConfigError(f"{path.name} must contain a JSON object.")
    return Config(_deep_merge(data, user_settings))
