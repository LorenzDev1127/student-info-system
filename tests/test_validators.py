import unittest

from src.utils.validators import (
    StudentRules,
    ValidationError,
    validate_course,
    validate_email,
    validate_gpa,
    validate_name,
    validate_year_level,
)


class TestFieldValidators(unittest.TestCase):
    def test_name_is_trimmed_and_spaces_collapsed(self):
        self.assertEqual(validate_name("  Juan   Dela  Cruz "), "Juan Dela Cruz")

    def test_name_allows_common_symbols(self):
        self.assertEqual(validate_name("Ma. Clara O'Neil-Santos"), "Ma. Clara O'Neil-Santos")

    def test_name_rejects_digits_and_blank(self):
        for bad in ("Juan 123", "", "   ", "A"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                validate_name(bad)

    def test_email_is_lowercased(self):
        self.assertEqual(validate_email(" Juan@School.EDU.ph "), "juan@school.edu.ph")

    def test_email_rejects_bad_format(self):
        for bad in ("juan", "juan@", "@school.com", "juan@school", ""):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                validate_email(bad)

    def test_course_is_uppercased(self):
        self.assertEqual(validate_course(" bsit "), "BSIT")

    def test_year_level_range(self):
        self.assertEqual(validate_year_level("3"), 3)
        for bad in ("0", "6", "third", ""):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                validate_year_level(bad)

    def test_gpa_optional_and_ranged(self):
        self.assertIsNone(validate_gpa(""))
        self.assertIsNone(validate_gpa(None))
        self.assertEqual(validate_gpa("1.756"), 1.76)
        for bad in ("0.5", "5.5", "abc"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                validate_gpa(bad)


class TestStudentRules(unittest.TestCase):
    def setUp(self):
        self.rules = StudentRules()
        self.valid = {"name": "Ana Reyes", "email": "ana@mail.com", "course": "bscs", "year_level": "2"}

    def test_validate_full_record(self):
        clean = self.rules.validate(self.valid)
        self.assertEqual(clean["course"], "BSCS")
        self.assertEqual(clean["year_level"], 2)

    def test_missing_required_field(self):
        del self.valid["email"]
        with self.assertRaises(ValidationError):
            self.rules.validate(self.valid)

    def test_read_only_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.rules.validate({"student_id": "HACKED"}, partial=True)

    def test_custom_limits(self):
        rules = StudentRules(max_year_level=4)
        with self.assertRaises(ValidationError):
            rules.validate_field("year_level", "5")


if __name__ == "__main__":
    unittest.main()
