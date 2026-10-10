"""Student Information System: command-line entry point.

Run from the project folder with either:
    python -m src.main
    python src/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable, Optional

# Allow "python src/main.py" (and VS Code's Run button) as well as "python -m src.main".
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.student import Student  # noqa: E402
from src.services.repository import JsonStudentRepository, StorageError  # noqa: E402
from src.services.student_service import (  # noqa: E402
    DuplicateStudentError,
    StudentNotFoundError,
    StudentService,
)
from src.utils import ui  # noqa: E402
from src.utils.config import Config, ConfigError, load_config  # noqa: E402
from src.utils.exporter import export_to_csv  # noqa: E402
from src.utils.logger import setup_logging  # noqa: E402
from src.utils.validators import StudentRules, ValidationError  # noqa: E402

TABLE_HEADERS = ("ID", "Name", "Email", "Course", "Year", "GPA")
USER_ERRORS = (ValidationError, DuplicateStudentError, StudentNotFoundError)


def format_gpa(gpa: Optional[float]) -> str:
    return f"{gpa:.2f}" if gpa is not None else "—"


def ordinal(number: int) -> str:
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th'."""
    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def student_row(student: Student) -> tuple:
    return (
        student.student_id,
        student.name,
        student.email,
        student.course,
        student.year_level,
        format_gpa(student.gpa),
    )


def show_student(student: Student) -> None:
    ui.card(
        student.name,
        [
            ("Student ID", student.student_id),
            ("Email", student.email),
            ("Course", student.course),
            ("Year level", f"{ordinal(student.year_level)} year"),
            ("GPA", format_gpa(student.gpa)),
            ("Created", student.created_at.replace("T", " ")),
            ("Updated", student.updated_at.replace("T", " ")),
        ],
    )


class StudentInformationSystem:
    """Menu-driven CLI on top of StudentService."""

    def __init__(self, service: StudentService, config: Config, logger: logging.Logger) -> None:
        self.service = service
        self.rules: StudentRules = service.rules
        self.config = config
        self.logger = logger
        self.menu: list[tuple[str, str, Optional[Callable[[], None]]]] = [
            ("1", "Add student", self.add_student),
            ("2", "View all students", self.view_all_students),
            ("3", "View student by ID", self.view_student),
            ("4", "Search students", self.search_students),
            ("5", "Update student", self.update_student),
            ("6", "Delete student", self.delete_student),
            ("7", "Export to CSV", self.export_students),
            ("8", "Statistics", self.show_statistics),
            ("0", "Exit", None),
        ]

    # ------------------------------------------------------------------ helpers
    def _field(self, name: str) -> Callable[[str], object]:
        """Parser for ui.ask that reuses the service's validation rules."""
        return lambda raw: self.rules.validate_field(name, raw)

    def _unique_email(self, exclude_id: str = "") -> Callable[[str], str]:
        """Validate an email and reject it right away if it is already taken."""

        def parse(raw: str) -> str:
            email = self.rules.validate_field("email", raw)
            for student in self.service.get_all_students(sort_by=""):
                if student.email == email and student.student_id != exclude_id:
                    raise ValidationError(f"That email is already used by {student.name}.")
            return email

        return parse

    def _ask_existing_student(self) -> Optional[Student]:
        student_id = ui.ask("Student ID")
        student = self.service.get_student(student_id)
        if student is None:
            ui.error(f"No student found with ID '{student_id}'.")
        return student

    # ------------------------------------------------------------------- screens
    def display_menu(self) -> None:
        ui.clear()
        count = len(self.service.get_all_students(sort_by=""))
        ui.banner(
            self.config.get("app.name", "Student Information System"),
            f"v{self.config.get('app.version', '1.0.0')}  ·  {count} student{'s' if count != 1 else ''} on file",
        )
        for key, label, _ in self.menu:
            print(f"   {ui.paint(f'[{key}]', 'cyan', 'bold')} {label}")
        print()

    def add_student(self) -> None:
        ui.section("Add New Student")
        r = self.rules
        data = {
            "name": ui.ask("Full name", self._field("name")),
            "email": ui.ask("Email", self._unique_email()),
            "course": ui.ask("Course (e.g. BSIT)", self._field("course")),
            "year_level": ui.ask(f"Year level ({r.min_year_level}-{r.max_year_level})", self._field("year_level")),
            "gpa": ui.ask(f"GPA ({r.min_gpa:.2f}-{r.max_gpa:.2f}, blank to skip)", self._field("gpa"), default=""),
        }
        student = self.service.add_student(data)
        print()
        ui.success(f"Student added with ID {ui.paint(student.student_id, 'bold')}")
        show_student(student)

    def view_all_students(self) -> None:
        ui.section("All Students")
        students = self.service.get_all_students()
        if not students:
            ui.info("No students yet. Choose [1] to add one.")
            return
        ui.table(TABLE_HEADERS, [student_row(s) for s in students])
        ui.info(f"{len(students)} record(s)")

    def view_student(self) -> None:
        ui.section("Find Student by ID")
        student = self._ask_existing_student()
        if student:
            show_student(student)

    def search_students(self) -> None:
        ui.section("Search Students")
        keyword = ui.ask("Search name, email, course or ID")
        results = self.service.search(keyword)
        if not results:
            ui.warning(f"No matches for '{keyword}'.")
            return
        ui.table(TABLE_HEADERS, [student_row(s) for s in results])
        ui.info(f"{len(results)} match(es) for '{keyword}'")

    def update_student(self) -> None:
        ui.section("Update Student")
        student = self._ask_existing_student()
        if not student:
            return
        show_student(student)
        ui.info("Press Enter to keep the current value.")

        r = self.rules
        answers = {
            "name": ui.ask("Full name", self._field("name"), default=student.name),
            "email": ui.ask("Email", self._unique_email(student.student_id), default=student.email),
            "course": ui.ask("Course", self._field("course"), default=student.course),
            "year_level": ui.ask(
                f"Year level ({r.min_year_level}-{r.max_year_level})",
                self._field("year_level"),
                default=str(student.year_level),
            ),
            "gpa": ui.ask(
                f"GPA ({r.min_gpa:.2f}-{r.max_gpa:.2f})",
                self._field("gpa"),
                default="" if student.gpa is None else str(student.gpa),
            ),
        }
        changes = {k: v for k, v in answers.items() if v != getattr(student, k)}
        if not changes:
            ui.info("Nothing changed.")
            return

        updated = self.service.update_student(student.student_id, changes)
        print()
        ui.success(f"Updated {', '.join(name.replace('_', ' ') for name in changes)}.")
        show_student(updated)

    def delete_student(self) -> None:
        ui.section("Delete Student")
        student = self._ask_existing_student()
        if not student:
            return
        show_student(student)
        if not ui.confirm(f"Delete {student.name} permanently?"):
            ui.info("Delete cancelled.")
            return
        self.service.delete_student(student.student_id)
        ui.success(f"Deleted {student.name} ({student.student_id}).")

    def export_students(self) -> None:
        ui.section("Export to CSV")
        students = self.service.get_all_students()
        if not students:
            ui.warning("There are no students to export.")
            return
        path = export_to_csv(students, self.config.path("export.directory"))
        self.logger.info("Exported %d students to %s", len(students), path.name)
        ui.success(f"Exported {len(students)} student(s) to {path.relative_to(self.config.root)}")

    def show_statistics(self) -> None:
        ui.section("Statistics")
        stats = self.service.statistics()
        if not stats["total"]:
            ui.info("No students yet.")
            return
        ui.info(f"Total students : {ui.paint(stats['total'], 'bold')}")
        ui.info(f"Average GPA    : {ui.paint(format_gpa(stats['average_gpa']), 'bold')}")
        print(ui.paint("\n  Students per course", "bold"))
        ui.bar_chart(stats["by_course"])
        print(ui.paint("\n  Students per year level", "bold"))
        ui.bar_chart({f"{ordinal(year)} year": n for year, n in stats["by_year_level"].items()})

    # ---------------------------------------------------------------- main loop
    def run(self) -> None:
        self.logger.info("Application started")
        actions = {key: action for key, _, action in self.menu}
        try:
            while True:
                self.display_menu()
                choice = input(f"  {ui.paint('›', 'cyan', 'bold')} Choose an option: ").strip()
                if choice == "0":
                    break
                action = actions.get(choice)
                if action is None:
                    ui.error(f"'{choice}' is not on the menu. Pick 0-8.")
                else:
                    self._run_action(action)
                ui.pause()
        except (KeyboardInterrupt, EOFError):
            print()
        print(ui.paint("\n  Goodbye!\n", "cyan"))
        self.logger.info("Application closed")

    def _run_action(self, action: Callable[[], None]) -> None:
        """Run one menu action without letting an error crash the app."""
        try:
            action()
        except KeyboardInterrupt:
            print()
            ui.warning("Cancelled.")
        except USER_ERRORS as exc:
            ui.error(str(exc))
        except StorageError as exc:
            self.logger.error("Storage problem: %s", exc)
            ui.error(f"Could not access the data file: {exc}")
        except Exception:  # last line of defence: log it, keep the app alive
            self.logger.exception("Unexpected error in %s", action.__name__)
            ui.error("Something went wrong. Details were written to logs/app.log.")


def main() -> int:
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = setup_logging(config)
    ui.init(
        use_colors=config.get("ui.use_colors", True),
        clear_screen=config.get("ui.clear_screen", True),
    )
    try:
        repository = JsonStudentRepository(
            config.path("storage.data_file"),
            backup_on_corrupt=config.get("storage.backup_on_corrupt", True),
        )
    except StorageError as exc:
        logger.critical("Cannot start: %s", exc)
        ui.error(str(exc))
        return 1

    service = StudentService(repository, StudentRules.from_config(config))
    StudentInformationSystem(service, config, logger).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
