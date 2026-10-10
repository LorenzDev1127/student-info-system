"""Input validation.

Every validator takes raw input (usually a string typed by the user), returns a
clean value, or raises ``ValidationError`` with a message that can be shown to
the user as-is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

from src.utils.config import Config

EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
NAME_SYMBOLS = " .'-"  # allowed besides letters, e.g. "Ma. Clara O'Neil-Cruz"


class ValidationError(ValueError):
    """Raised when user input is invalid."""


def validate_name(value: Any) -> str:
    name = " ".join(str(value).split())  # trim and collapse inner spaces
    if not name:
        raise ValidationError("Name is required.")
    if len(name) > 100:
        raise ValidationError("Name must be 100 characters or fewer.")
    if not all(ch.isalpha() or ch in NAME_SYMBOLS for ch in name):
        raise ValidationError("Name may only contain letters, spaces, periods, apostrophes and hyphens.")
    if sum(ch.isalpha() for ch in name) < 2:
        raise ValidationError("Name must contain at least 2 letters.")
    return name


def validate_email(value: Any) -> str:
    email = str(value).strip().lower()
    if not email:
        raise ValidationError("Email is required.")
    if not EMAIL_PATTERN.match(email):
        raise ValidationError(f"'{email}' is not a valid email address.")
    return email


def validate_course(value: Any) -> str:
    course = " ".join(str(value).split()).upper()
    if not course:
        raise ValidationError("Course is required.")
    if not 2 <= len(course) <= 50:
        raise ValidationError("Course must be 2 to 50 characters long.")
    return course


def validate_year_level(value: Any, minimum: int = 1, maximum: int = 5) -> int:
    try:
        year = int(str(value).strip())
    except ValueError:
        raise ValidationError("Year level must be a whole number.") from None
    if not minimum <= year <= maximum:
        raise ValidationError(f"Year level must be between {minimum} and {maximum}.")
    return year


def validate_gpa(value: Any, minimum: float = 1.0, maximum: float = 5.0) -> Optional[float]:
    """GPA is optional: blank or None means 'not recorded yet'."""
    if value is None or str(value).strip() == "":
        return None
    try:
        gpa = float(str(value).strip())
    except ValueError:
        raise ValidationError("GPA must be a number, e.g. 1.75.") from None
    if not minimum <= gpa <= maximum:
        raise ValidationError(f"GPA must be between {minimum:.2f} and {maximum:.2f}.")
    return round(gpa, 2)


@dataclass(frozen=True)
class StudentRules:
    """Validation rules for student fields, loaded from configuration."""

    id_prefix: str = "STU"
    min_year_level: int = 1
    max_year_level: int = 5
    min_gpa: float = 1.0
    max_gpa: float = 5.0

    REQUIRED = ("name", "email", "course", "year_level")

    @classmethod
    def from_config(cls, config: Config) -> "StudentRules":
        return cls(
            id_prefix=config.get("students.id_prefix", cls.id_prefix),
            min_year_level=int(config.get("students.min_year_level", cls.min_year_level)),
            max_year_level=int(config.get("students.max_year_level", cls.max_year_level)),
            min_gpa=float(config.get("students.min_gpa", cls.min_gpa)),
            max_gpa=float(config.get("students.max_gpa", cls.max_gpa)),
        )

    def _validators(self) -> dict[str, Callable[[Any], Any]]:
        return {
            "name": validate_name,
            "email": validate_email,
            "course": validate_course,
            "year_level": lambda v: validate_year_level(v, self.min_year_level, self.max_year_level),
            "gpa": lambda v: validate_gpa(v, self.min_gpa, self.max_gpa),
        }

    def validate_field(self, field_name: str, value: Any) -> Any:
        validators = self._validators()
        if field_name not in validators:
            raise ValidationError(f"Unknown field: {field_name}")
        return validators[field_name](value)

    def validate(self, data: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
        """Validate a whole record (or only the given fields when ``partial``)."""
        unknown = set(data) - set(self._validators())
        if unknown:
            raise ValidationError(f"Unknown or read-only field(s): {', '.join(sorted(unknown))}")
        if not partial:
            missing = [name for name in self.REQUIRED if name not in data]
            if missing:
                raise ValidationError(f"Missing required field(s): {', '.join(missing)}")
        return {name: self.validate_field(name, value) for name, value in data.items()}
