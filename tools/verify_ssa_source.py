"""Offline verification of the pinned CSV against retained SSA HTML.

Run from the project root: python -B tools/verify_ssa_source.py
No network calls, profile access, or file writes.
"""

import csv
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/sources/ssa_2021_tr2024.html"
DATA = ROOT / "death_clock/data/ssa_2021_tr2024.csv"
SOURCE_SHA256 = "54a7ba64bba1d36c0c8269784c4f4392dbc2de010da2c8ff944e8e08acfe5f73"
DATA_SHA256 = "9de6f7c4c116c956f5d12b1712405b148350d612ee8f7a320589814e79da81bd"


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cells, self.cell = [], [], None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.cells = []
        if tag == "td":
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.cells.append("".join(self.cell).strip())
            self.cell = None
        if tag == "tr" and len(self.cells) == 7 and self.cells[0].isdigit():
            self.rows.append((int(self.cells[0]), Decimal(self.cells[3]), Decimal(self.cells[6])))


def source_rows():
    html = SOURCE.read_text(encoding="utf-8")
    assert "Period Life Table, 2021, as used in the 2024 Trustees Report" in html
    assert 'abbr="male life expectancy"' in html
    assert 'abbr="female life expectancy"' in html
    parser = TableParser()
    parser.feed(html)
    assert [row[0] for row in parser.rows] == list(range(120))
    return parser.rows


def verify():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256, "Source snapshot changed"
    assert sha256(DATA.read_bytes()).hexdigest() == DATA_SHA256, "Extracted CSV changed"
    with DATA.open(encoding="utf-8", newline="") as stream:
        actual = [(int(r["age"]), Decimal(r["male"]), Decimal(r["female"])) for r in csv.DictReader(stream)]
    assert actual == source_rows(), "CSV differs from the official source snapshot"
    return actual


if __name__ == "__main__":
    rows = verify()
    print(f"Verified {len(rows)} ages / {2 * len(rows)} expectancy values against the pinned SSA snapshot.")
