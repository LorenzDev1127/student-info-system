import re
import unittest

from src.models.student import Student, generate_student_id


class TestStudentModel(unittest.TestCase):
    def test_generated_id_format(self):
        self.assertRegex(generate_student_id("SIS"), re.compile(r"^SIS-[0-9A-F]{6}$"))

    def test_round_trip(self):
        student = Student(name="Ana Reyes", email="ana@mail.com", course="BSIT", year_level=3, gpa=1.5)
        self.assertEqual(Student.from_dict(student.to_dict()), student)

    def test_from_dict_ignores_unknown_keys(self):
        data = Student(name="Ana", email="a@b.co", course="BSIT", year_level=1).to_dict()
        data["nickname"] = "ignored"
        self.assertEqual(Student.from_dict(data).name, "Ana")

    def test_from_dict_missing_field_raises(self):
        with self.assertRaises(TypeError):
            Student.from_dict({"name": "Ana"})


if __name__ == "__main__":
    unittest.main()
