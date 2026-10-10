"""Export student records to CSV (opens cleanly in Excel / Google Sheets)."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.models.student import Student

EXPORT_COLUMNS = [
    "student_id",
    "name",
    "email",
    "course",
    "year_level",
    "gpa",
    "created_at",
    "updated_at",
]


def export_to_csv(students: Iterable[Student], directory: Path) -> Path:
    """Write students to a timestamped CSV file and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"students_{datetime.now():%Y%m%d_%H%M%S}.csv"

    # utf-8-sig adds a BOM so Excel shows names like "Peñafrancia" correctly.
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for student in students:
            writer.writerow(student.to_dict())
    return path
