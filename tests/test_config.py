import tempfile
import unittest
from pathlib import Path

from src.utils.config import ConfigError, load_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "config.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_file_uses_defaults(self):
        config = load_config(self.path)
        self.assertEqual(config.get("students.id_prefix"), "STU")

    def test_file_overrides_only_given_keys(self):
        self.path.write_text('{"students": {"id_prefix": "SIS"}}')
        config = load_config(self.path)
        self.assertEqual(config.get("students.id_prefix"), "SIS")
        self.assertEqual(config.get("students.max_year_level"), 5)  # default kept

    def test_invalid_json_raises(self):
        self.path.write_text("{ nope")
        with self.assertRaises(ConfigError):
            load_config(self.path)

    def test_relative_paths_resolve_to_project_root(self):
        config = load_config(self.path)
        self.assertTrue(config.path("storage.data_file").is_absolute())


if __name__ == "__main__":
    unittest.main()
