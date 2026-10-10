"""Student business logic: CRUD, search and statistics.

The service validates every change, keeps emails and IDs unique, and talks to
storage only through the repository.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Optional

from src.models.student import Student, generate_student_id
from src.services.repository import JsonStudentRepository
from src.utils.validators import StudentRules

logger = logging.getLogger("sis.service")


class StudentNotFoundError(LookupError):
    """Raised when no student has the given ID."""

    def __init__(self, student_id: str) -> None:
        super().__init__(f"No student found with ID '{student_id}'.")
        self.student_id = student_id


class DuplicateStudentError(ValueError):
    """Raised when another student already uses the same email."""


def _normalize_id(student_id: str) -> str:
    return str(student_id).strip().upper()


class StudentService:
    def __init__(self, repository: JsonStudentRepository, rules: Optional[StudentRules] = None) -> None:
        self.repository = repository
        self.rules = rules or StudentRules()

    # ------------------------------------------------------------------ load/save
    def _load(self) -> list[Student]:
        """Load all students, skipping (and logging) any malformed record."""
        students = []
        for index, record in enumerate(self.repository.load_all()):
            try:
                students.append(Student.from_dict(record))
            except (TypeError, AttributeError) as exc:
                logger.warning("Skipped malformed record #%d: %s", index, exc)
        return students

    def _save(self, students: list[Student]) -> None:
        self.repository.save_all([student.to_dict() for student in students])

    @staticmethod
    def _find(students: list[Student], student_id: str) -> Optional[Student]:
        wanted = _normalize_id(student_id)
        return next((s for s in students if _normalize_id(s.student_id) == wanted), None)

    @staticmethod
    def _ensure_unique_email(students: list[Student], email: str, exclude_id: str = "") -> None:
        for student in students:
            if student.email == email and student.student_id != exclude_id:
                raise DuplicateStudentError(
                    f"Email '{email}' is already used by {student.name} ({student.student_id})."
                )

    # ---------------------------------------------------------------------- CRUD
    def add_student(self, data: dict[str, Any]) -> Student:
        clean = self.rules.validate(data)
        students = self._load()
        self._ensure_unique_email(students, clean["email"])

        existing_ids = {_normalize_id(s.student_id) for s in students}
        student_id = generate_student_id(self.rules.id_prefix)
        while student_id in existing_ids:  # practically never loops, but be safe
            student_id = generate_student_id(self.rules.id_prefix)

        student = Student(student_id=student_id, **clean)
        students.append(student)
        self._save(students)
        logger.info("Added student %s (%s)", student.student_id, student.name)
        return student

    def get_all_students(self, sort_by: str = "name") -> list[Student]:
        students = self._load()
        if sort_by:
            students.sort(key=lambda s: str(getattr(s, sort_by, "")).lower())
        return students

    def get_student(self, student_id: str) -> Optional[Student]:
        return self._find(self._load(), student_id)

    def update_student(self, student_id: str, changes: dict[str, Any]) -> Student:
        clean = self.rules.validate(changes, partial=True)  # also blocks id/created_at edits
        students = self._load()
        student = self._find(students, student_id)
        if student is None:
            raise StudentNotFoundError(student_id)
        if "email" in clean:
            self._ensure_unique_email(students, clean["email"], exclude_id=student.student_id)

        for field_name, value in clean.items():
            setattr(student, field_name, value)
        student.touch()
        self._save(students)
        logger.info("Updated student %s: %s", student.student_id, ", ".join(clean) or "no fields")
        return student

    def delete_student(self, student_id: str) -> Student:
        """Delete a student and return the removed record."""
        students = self._load()
        student = self._find(students, student_id)
        if student is None:
            raise StudentNotFoundError(student_id)
        students.remove(student)
        self._save(students)
        logger.info("Deleted student %s (%s)", student.student_id, student.name)
        return student

    # ---------------------------------------------------------- search and stats
    def search(self, keyword: str) -> list[Student]:
        """Case-insensitive match on ID, name, email or course."""
        term = keyword.strip().lower()
        if not term:
            return []
        return [
            s
            for s in self.get_all_students()
            if any(term in str(value).lower() for value in (s.student_id, s.name, s.email, s.course))
        ]

    def statistics(self) -> dict[str, Any]:
        students = self._load()
        gpas = [s.gpa for s in students if s.gpa is not None]
        return {
            "total": len(students),
            "average_gpa": round(sum(gpas) / len(gpas), 2) if gpas else None,
            "by_course": dict(Counter(s.course for s in students).most_common()),
            "by_year_level": dict(sorted(Counter(s.year_level for s in students).items())),
        }
