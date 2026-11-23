import json
import tempfile
import unittest
from pathlib import Path

from config import SAMPLE_FAQ_PATH
from services.app_context import AppContext


def sample_faqs() -> list[dict]:
    rows = json.loads(Path(SAMPLE_FAQ_PATH).read_text(encoding="utf-8"))
    for i, row in enumerate(rows, start=1):
        row["id"] = i
    return rows


class ContextTestCase(unittest.TestCase):
    """Each test gets a brand-new SQLite file seeded with the sample FAQs."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ctx = AppContext(db_path=Path(self._tmp.name) / "test.db")

    def tearDown(self):
        self._tmp.cleanup()
