import json
import tempfile
import unittest
from pathlib import Path

from src.services.repository import JsonStudentRepository


class TestJsonStudentRepository(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_file = Path(self._tmp.name) / "data" / "students.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_creates_missing_file_and_folder(self):
        JsonStudentRepository(self.data_file)
        self.assertEqual(json.loads(self.data_file.read_text()), [])

    def test_save_and_load(self):
        repo = JsonStudentRepository(self.data_file)
        repo.save_all([{"name": "Ana"}])
        self.assertEqual(repo.load_all(), [{"name": "Ana"}])
        self.assertFalse(self.data_file.with_name("students.json.tmp").exists())

    def test_recovers_from_corrupted_json(self):
        repo = JsonStudentRepository(self.data_file)
        self.data_file.write_text("{ this is not json", encoding="utf-8")

        with self.assertLogs("sis.storage", level="WARNING"):
            self.assertEqual(repo.load_all(), [])

        backups = list(self.data_file.parent.glob("students.corrupt-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "{ this is not json")
        self.assertEqual(json.loads(self.data_file.read_text()), [])

    def test_recovers_when_top_level_is_not_a_list(self):
        repo = JsonStudentRepository(self.data_file)
        self.data_file.write_text('{"name": "Ana"}', encoding="utf-8")
        with self.assertLogs("sis.storage", level="WARNING"):
            self.assertEqual(repo.load_all(), [])

    def test_empty_file_is_treated_as_empty_list(self):
        repo = JsonStudentRepository(self.data_file)
        self.data_file.write_text("", encoding="utf-8")
        self.assertEqual(repo.load_all(), [])


if __name__ == "__main__":
    unittest.main()
