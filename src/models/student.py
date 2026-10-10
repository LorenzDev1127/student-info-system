"""Student model.

A plain dataclass that knows how to turn itself into a dictionary (for JSON
storage) and back. It does no validation itself; that is the service's job.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from typing import Any, ClassVar, Optional


def _now() -> str:
    """Current local time as an ISO 8601 string, e.g. '2026-10-10T19:47:13'."""
    return datetime.now().isoformat(timespec="seconds")


def generate_student_id(prefix: str = "STU") -> str:
    """Return a short random ID such as 'STU-4F9A2C'."""
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


@dataclass
class Student:
    """A single student record."""

    name: str
    email: str
    course: str
    year_level: int
    gpa: Optional[float] = None
    student_id: str = field(default_factory=generate_student_id)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    # Fields a user is allowed to change after the record is created.
    EDITABLE_FIELDS: ClassVar[tuple[str, ...]] = (
        "name",
        "email",
        "course",
        "year_level",
        "gpa",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the student to a JSON-friendly dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Student":
        """Build a Student from a stored dictionary, ignoring unknown keys.

        Raises TypeError if a required field is missing.
        """
        known = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in known})

    def touch(self) -> None:
        """Mark the record as modified now."""
        self.updated_at = _now()
