"""JSON storage for student records.

This layer only reads and writes raw dictionaries. Keeping file handling here
means the service could switch to XML, SQLite or a cloud database by swapping
this one class.

Safety features:
* Atomic saves: data is written to a temp file and then swapped in, so a crash
  mid-save can never leave a half-written students.json.
* Corruption recovery: if the file is not valid JSON, it is backed up to
  ``students.corrupt-<timestamp>.json`` and a fresh empty file is started.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("sis.storage")


class StorageError(Exception):
    """Raised when student data cannot be read or written."""


class JsonStudentRepository:
    def __init__(self, data_file: Path, backup_on_corrupt: bool = True) -> None:
        self.data_file = Path(data_file)
        self.backup_on_corrupt = backup_on_corrupt
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.data_file.exists():
                self.save_all([])
                logger.info("Created new data file at %s", self.data_file)
        except OSError as exc:
            raise StorageError(f"Cannot create data file: {exc}") from exc

    def load_all(self) -> list[dict[str, Any]]:
        try:
            text = self.data_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Data file disappeared; starting with an empty list.")
            self._ensure_data_file()
            return []
        except OSError as exc:
            raise StorageError(f"Cannot read {self.data_file.name}: {exc}") from exc

        if not text.strip():
            return []
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return self._recover(f"invalid JSON at line {exc.lineno}")
        if not isinstance(data, list):
            return self._recover("top-level value is not a list")
        return data

    def save_all(self, records: list[dict[str, Any]]) -> None:
        temp_file = self.data_file.with_name(self.data_file.name + ".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as file:
                json.dump(records, file, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.data_file)  # atomic on Windows and Linux
        except OSError as exc:
            raise StorageError(f"Cannot save {self.data_file.name}: {exc}") from exc

    def _recover(self, reason: str) -> list[dict[str, Any]]:
        """Back up a corrupted data file and start fresh."""
        backup = None
        if self.backup_on_corrupt:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.data_file.with_name(f"{self.data_file.stem}.corrupt-{stamp}.json")
            shutil.copy2(self.data_file, backup)
        self.save_all([])
        logger.warning(
            "Data file was corrupted (%s). Backup: %s. Started a fresh file.",
            reason,
            backup.name if backup else "none",
        )
        return []
