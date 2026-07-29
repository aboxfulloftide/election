from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from xlsx_reader import column_index


class XlsxReaderTests(TestCase):
    def test_column_index_converts_excel_letters(self) -> None:
        self.assertEqual(column_index("A1"), 0)
        self.assertEqual(column_index("Z1"), 25)
        self.assertEqual(column_index("AA1"), 26)
        self.assertEqual(column_index("AB42"), 27)
