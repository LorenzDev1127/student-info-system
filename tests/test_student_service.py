import json
import tempfile
import unittest
from pathlib import Path

from src.services.repository import JsonStudentRepository
from src.services.student_service import (
    DuplicateStudentError,
    StudentNotFoundError,
    StudentService,
)
from src.utils.validators import StudentRules, ValidationError


def sample(**overrides):
    data = {"name": "Ana Reyes", "email": "ana@mail.com", "course": "BSIT", "year_level": 3, "gpa": 1.5}
    data.update(overrides)
    return data


class TestStudentService(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_file = Path(self._tmp.name) / "students.json"
        self.service = self._new_service()

    def tearDown(self):
        self._tmp.cleanup()

    def _new_service(self):
        return StudentService(JsonStudentRepository(self.data_file), StudentRules(id_prefix="TST"))

    # ------------------------------------------------------------------ create
    def test_add_student_assigns_id_and_persists(self):
        student = self.service.add_student(sample())
        self.assertTrue(student.student_id.startswith("TST-"))
        # A brand-new service reading the same file sees the record.
        self.assertEqual(self._new_service().get_student(student.student_id), student)

    def test_add_student_validates_input(self):
        with self.assertRaises(ValidationError):
            self.service.add_student(sample(email="not-an-email"))
        self.assertEqual(self.service.get_all_students(), [])

    def test_duplicate_email_rejected(self):
        self.service.add_student(sample())
        with self.assertRaises(DuplicateStudentError):
            self.service.add_student(sample(name="Other Person", email="ANA@mail.com"))

    # -------------------------------------------------------------------- read
    def test_get_student_is_case_insensitive(self):
        student = self.service.add_student(sample())
        self.assertEqual(self.service.get_student(student.student_id.lower()), student)

    def test_get_missing_student_returns_none(self):
        self.assertIsNone(self.service.get_student("TST-000000"))

    def test_get_all_sorted_by_name(self):
        self.service.add_student(sample(name="Zed Cruz", email="z@mail.com"))
        self.service.add_student(sample(name="Ana Reyes", email="a@mail.com"))
        self.assertEqual([s.name for s in self.service.get_all_students()], ["Ana Reyes", "Zed Cruz"])

    # ------------------------------------------------------------------ update
    def test_update_student(self):
        student = self.service.add_student(sample())
        updated = self.service.update_student(student.student_id, {"course": "bscs", "year_level": "4"})
        self.assertEqual((updated.course, updated.year_level), ("BSCS", 4))
        self.assertEqual(self.service.get_student(student.student_id).course, "BSCS")

    def test_update_cannot_change_id(self):
        student = self.service.add_student(sample())
        with self.assertRaises(ValidationError):
            self.service.update_student(student.student_id, {"student_id": "TST-HACKED"})

    def test_update_missing_student(self):
        with self.assertRaises(StudentNotFoundError):
            self.service.update_student("TST-000000", {"name": "Nobody"})

    def test_update_email_to_one_already_taken(self):
        self.service.add_student(sample())
        other = self.service.add_student(sample(name="Ben Lim", email="ben@mail.com"))
        with self.assertRaises(DuplicateStudentError):
            self.service.update_student(other.student_id, {"email": "ana@mail.com"})

    # ------------------------------------------------------------------ delete
    def test_delete_student(self):
        student = self.service.add_student(sample())
        deleted = self.service.delete_student(student.student_id)
        self.assertEqual(deleted.student_id, student.student_id)
        self.assertIsNone(self.service.get_student(student.student_id))

    def test_delete_missing_student(self):
        with self.assertRaises(StudentNotFoundError):
            self.service.delete_student("TST-000000")

    # ---------------------------------------------------------- search & stats
    def test_search_matches_name_email_and_course(self):
        self.service.add_student(sample())
        self.service.add_student(sample(name="Ben Lim", email="ben@mail.com", course="BSCS"))
        self.assertEqual(len(self.service.search("bscs")), 1)
        self.assertEqual(len(self.service.search("mail.com")), 2)
        self.assertEqual(self.service.search("   "), [])

    def test_statistics(self):
        self.service.add_student(sample(gpa=1.5))
        self.service.add_student(sample(name="Ben Lim", email="ben@mail.com", gpa=2.5, year_level=1))
        self.service.add_student(sample(name="Cy Tan", email="cy@mail.com", gpa=None))
        stats = self.service.statistics()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["average_gpa"], 2.0)
        self.assertEqual(stats["by_course"], {"BSIT": 3})
        self.assertEqual(stats["by_year_level"], {1: 1, 3: 2})

    # ---------------------------------------------------------------- recovery
    def test_malformed_records_are_skipped(self):
        good = self.service.add_student(sample())
        records = json.loads(self.data_file.read_text())
        records.append({"name": "missing everything else"})
        self.data_file.write_text(json.dumps(records))

        with self.assertLogs("sis.service", level="WARNING"):
            students = self.service.get_all_students()
        self.assertEqual([s.student_id for s in students], [good.student_id])


if __name__ == "__main__":
    unittest.main()
