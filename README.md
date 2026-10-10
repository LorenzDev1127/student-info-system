# Student Information System

A command-line Student Information System written in Python. It manages student
records (add, view, search, update, delete), stores them as JSON, and is built
with a modular, cloud-ready structure: external configuration, layered
services, logging, and error recovery.

**Author:** Florenz A. Valdez · BSIT 3A

---

## Features

| Area | What it does |
|------|--------------|
| **CRUD** | Add, view all, view by ID, update and delete students |
| **Search** | Case-insensitive search across ID, name, email and course |
| **Statistics** | Total students, average GPA, bar charts per course and year level |
| **Export** | One-click export to a timestamped CSV file (opens in Excel) |
| **Validation** | Name, email, course, year level and GPA are checked as you type; duplicate emails are blocked |
| **Persistence** | JSON storage with atomic saves (no half-written files) |
| **Error recovery** | A corrupted `students.json` is backed up and replaced; malformed records are skipped and logged; the app never crashes on a bad action |
| **Configuration** | All settings live in `config/config.json` |
| **Logging** | Rotating log file at `logs/app.log` |
| **Tests** | 40 unit tests using the built-in `unittest` module |

No third-party packages are needed. Python 3.9 or newer is enough.

## Project structure

```
student-info-system/
├── src/
│   ├── main.py                    # CLI menu (entry point)
│   ├── models/
│   │   └── student.py             # Student dataclass
│   ├── services/
│   │   ├── repository.py          # JSON file storage (atomic save, corruption recovery)
│   │   └── student_service.py     # Business logic: CRUD, search, statistics
│   └── utils/
│       ├── config.py              # Loads config/config.json over defaults
│       ├── logger.py              # Rotating file logger
│       ├── validators.py          # Input validation rules
│       ├── exporter.py            # CSV export
│       └── ui.py                  # Colors, tables, cards, prompts
├── data/students.json             # Student records
├── config/config.json             # App settings
├── logs/                          # app.log is written here
├── tests/                         # Unit tests
├── requirements.txt
└── .gitignore
```

Each layer has one job: `main.py` only talks to the user, `StudentService`
holds the rules, and `JsonStudentRepository` is the only code that touches the
file. Swapping JSON for a cloud database would mean replacing one class.

## Getting started

```bash
git clone https://github.com/<your-username>/student-info-system.git
cd student-info-system
python -m src.main
```

`python src/main.py` (or the Run button in VS Code) also works.

### Example

```
╔═══════════════════════════════════════╗
║       Student Information System      ║
║     v1.0.0  ·  3 students on file     ║
╚═══════════════════════════════════════╝
   [1] Add student
   [2] View all students
   [3] View student by ID
   [4] Search students
   [5] Update student
   [6] Delete student
   [7] Export to CSV
   [8] Statistics
   [0] Exit

── All Students ──────────────────────────────────
┌────────────┬────────────────────┬──────────────────────────────┬────────┬──────┬──────┐
│ ID         │ Name               │ Email                        │ Course │ Year │ GPA  │
├────────────┼────────────────────┼──────────────────────────────┼────────┼──────┼──────┤
│ STU-7A8B9C │ Jose Rizal Mercado │ jose.mercado@example.edu.ph  │ BSIT   │ 4    │ 2.00 │
│ STU-1A2B3C │ Juan Dela Cruz     │ juan.delacruz@example.edu.ph │ BSIT   │ 3    │ 1.75 │
│ STU-4D5E6F │ Maria Santos       │ maria.santos@example.edu.ph  │ BSCS   │ 2    │ 1.50 │
└────────────┴────────────────────┴──────────────────────────────┴────────┴──────┴──────┘
```

## Configuration

Edit `config/config.json`. Missing keys fall back to built-in defaults.

| Key | Default | Meaning |
|-----|---------|---------|
| `storage.data_file` | `data/students.json` | Where records are saved |
| `storage.backup_on_corrupt` | `true` | Back up a broken data file before resetting it |
| `logging.level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `logging.console` | `false` | Also print log lines to the terminal |
| `export.directory` | `exports` | Where CSV exports go |
| `students.id_prefix` | `STU` | Prefix for generated IDs (`STU-4F9A2C`) |
| `students.min_year_level` / `max_year_level` | `1` / `5` | Allowed year levels |
| `students.min_gpa` / `max_gpa` | `1.0` / `5.0` | Allowed GPA range (PH 1.00–5.00 scale) |
| `ui.use_colors` | `true` | Colored output (auto-off when output is redirected) |
| `ui.clear_screen` | `true` | Clear the screen before showing the menu |

## Running the tests

```bash
python -m unittest discover -s tests -v
# or, if pytest is installed:
pytest
```

The tests use temporary folders, so they never touch your real `data/students.json`.

## Error handling and logging

* Invalid input is rejected with a clear message and the prompt repeats.
* `Ctrl+C` during an action cancels just that action; at the menu it exits cleanly.
* Unexpected errors are written to `logs/app.log` with a full traceback while the app keeps running.
* Saves go to a temporary file first and are then swapped in, so a crash can't corrupt the data.
* If `students.json` is corrupted, it is copied to `students.corrupt-<timestamp>.json` and a fresh file is started.

Sample log:

```
2026-10-10 19:59:11 | INFO     | sis.service  | Added student STU-67088E (Ana Reyes)
2026-10-10 19:59:15 | WARNING  | sis.storage  | Data file was corrupted (invalid JSON at line 1). Backup: students.corrupt-20261010_195915.json. Started a fresh file.
```

## Fixes to the provided sample code

| Problem in the sample | Fix |
|-----------------------|-----|
| `student_service.py` used `datetime` without importing it (crash on update) | Timestamps handled by the model's `touch()` method |
| `Student(**student_data)` crashed because `student_id` was a required argument the menu never sent | `student_id` is now auto-generated with a default |
| `delete_student` compared the list length after saving, so it always returned `False` | Returns the deleted student or raises `StudentNotFoundError` |
| Update and delete menu options were `pass` | Fully implemented with confirmation |
| `from ..models...` relative import failed when running `main.py` | Absolute `src.` imports; both run commands work |
| `logs/app.log` handler crashed if `logs/` didn't exist | Folder is created automatically |
| File name mismatch (`student_services.py` vs `student_service.py`) | Consistent naming |
| No validation, duplicate checks or config file | Added `validators.py`, unique-email check and `config.json` |
| Updates could overwrite `student_id` / `created_at` | Only editable fields are accepted |

## Git workflow

Work happens on feature branches that are merged into `main`:

```bash
git checkout -b feature/student-model
git add src/models
git commit -m "feat(model): add Student dataclass with to_dict/from_dict"
git push -u origin feature/student-model
# open a Pull Request on GitHub, review, then merge into main
```

Branches used: `feature/student-model`, `feature/storage-config`,
`feature/student-service`, `feature/cli-menu`, `test/unit-tests`, `docs/readme`.

Commit messages follow the `type(scope): summary` style
(`feat`, `fix`, `test`, `docs`, `refactor`, `chore`).

## License

Made for academic purposes.
