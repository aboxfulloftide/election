#!/usr/bin/env python3
"""Generate normalized summaries from the first staged legacy formats."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
IDAHO_DIR = ROOT_DIR / "data/raw/official/idaho/legacy"
DELAWARE_DIR = ROOT_DIR / "data/raw/official/delaware/legacy"
ILLINOIS_DIR = ROOT_DIR / "data/raw/official/illinois/legacy"

PARTIES = {
    "DEM": "DEMOCRAT", "REPUBLICAN": "REPUBLICAN", "REP": "REPUBLICAN",
    "DEMOCRATIC": "DEMOCRAT", "DEMOCRATIC PARTY": "DEMOCRAT", "REPUBLICAN PARTY": "REPUBLICAN",
    "GREEN": "GREEN", "GREEN PARTY": "GREEN", "LIB": "LIBERTARIAN",
    "LIBERTARIAN PARTY": "LIBERTARIAN", "IND": "INDEPENDENT", "CON": "CONSTITUTION",
    "NON": "NONPARTISAN",
}
DATES = {2014: "11/04/2014", 2016: "11/08/2016", 2018: "11/06/2018"}


def integer(value: str) -> int:
    return int(re.sub(r"[^0-9-]", "", value or "") or 0)


def contest_record(state: str, state_po: str, year: int, office: str, name: str, candidates: list[dict[str, Any]], source_url: str, source_format: str, quality_grade: str, district: int | None = None) -> dict[str, Any]:
    candidates = sorted(candidates, key=lambda item: (-item["votes"], item["candidate"]))
    record: dict[str, Any] = {
        "office": office,
        "name": name,
        "state": state,
        "state_po": state_po,
        "year": year,
        "election_date": DATES[year],
        "source_url": source_url,
        "source_format": source_format,
        "quality_grade": quality_grade,
        "official": True,
        "total_votes": sum(item["votes"] for item in candidates),
        "winner": candidates[0],
        "margin_votes": candidates[0]["votes"] - (candidates[1]["votes"] if len(candidates) > 1 else candidates[0]["votes"]),
        "candidates": candidates,
    }
    if district is not None:
        record["district_number"] = district
        record["district_label"] = f"{district} {office} District"
    return record


def summary(state: str, state_po: str, source_name: str, source_url: str, elections: list[dict[str, Any]], quality_grade: str) -> dict[str, Any]:
    return {
        "source": {"name": source_name, "url": source_url, "official": True, "quality_grade": quality_grade},
        "state_po": state_po,
        "elections": elections,
    }


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"} and self.current_row is not None:
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.current_row is not None and self.current_cell is not None:
            self.current_row.append(re.sub(r"\s+", " ", "".join(self.current_cell)).strip())
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None:
            self.rows.append(self.current_row)
            self.current_row = None

    def handle_data(self, data: str) -> None:
        if self.current_cell is not None:
            self.current_cell.append(data)


def parse_idaho(year: int) -> dict[str, Any]:
    path = IDAHO_DIR / f"idaho_{year}_general_statewide_totals.html"
    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    contests: list[dict[str, Any]] = []
    current: tuple[str, int | None, str] | None = None
    office_patterns = [
        (re.compile(r"United States President", re.I), "President"),
        (re.compile(r"United States Senator", re.I), "U.S. Senate"),
        (re.compile(r"United States Representative - District (\d+)", re.I), "U.S. House"),
        (re.compile(r"Governor$", re.I), "Governor"),
    ]
    candidates: list[dict[str, Any]] = []

    def flush() -> None:
        nonlocal candidates
        if current and candidates:
            office, district, label = current
            contests.append(contest_record("Idaho", "ID", year, office, f"Idaho {year} {label}", candidates, "https://archive.sos.idaho.gov/ELECT/results/index.html", "idaho-official-html", "B", district))
        candidates = []

    for row in parser.rows:
        if len(row) == 1:
            heading = row[0]
            parsed = None
            for pattern, office in office_patterns:
                match = pattern.fullmatch(heading)
                if match:
                    district = int(match.group(1)) if match.lastindex else None
                    parsed = (office, district, heading)
                    break
            if parsed:
                flush()
                current = parsed
            elif current:
                flush()
                current = None
            continue
        if not current or len(row) < 3:
            continue
        party = PARTIES.get(row[0].upper(), "OTHER")
        candidate = row[1].strip()
        if not candidate or not re.search(r"\d", row[2]):
            continue
        candidates.append({"candidate": candidate, "party": party, "votes": integer(row[2])})
    flush()
    return summary("Idaho", "ID", "Idaho Secretary of State official election archive", "https://archive.sos.idaho.gov/ELECT/results/index.html", [{"election": {"state": "Idaho", "state_po": "ID", "year": year, "name": f"Idaho {year} General Election"}, "contests": contests}], "B")


def parse_delaware_2018() -> dict[str, Any]:
    path = DELAWARE_DIR / "delaware_2018_election.txt"
    current: tuple[str, int | None, str] | None = None
    party = "OTHER"
    grouped: dict[tuple[str, int | None], list[dict[str, Any]]] = defaultdict(list)
    heading_patterns = [
        (re.compile(r"UNITED STATES SENATOR$"), "U.S. Senate"),
        (re.compile(r"REPRESENTATIVE IN CONGRESS$"), "U.S. House"),
        (re.compile(r"STATE SENATOR DISTRICT (\d+)$"), "State Senate"),
        (re.compile(r"STATE REPRESENTATIVE DISTRICT (\d+)$"), "State House"),
    ]
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = [part.rstrip() for part in raw.split(";")]
        raw_first = fields[0]
        first = raw_first.strip()
        parsed = None
        for pattern, office in heading_patterns:
            match = pattern.fullmatch(first)
            if match:
                parsed = (office, int(match.group(1)) if match.lastindex else None, first)
                break
        if parsed:
            current = parsed
            party = "OTHER"
            continue
        if not current:
            continue
        if first.upper() in PARTIES:
            party = PARTIES[first.upper()]
            continue
        if not raw_first.startswith(" ") or len(fields) < 4 or not re.search(r"\d", fields[3]):
            continue
        grouped[(current[0], current[1])].append({"candidate": first, "party": party, "votes": integer(fields[3])})
    contests = []
    for (office, district), candidates in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1] or 0)):
        label = f"{office} District {district}" if district else office
        contests.append(contest_record("Delaware", "DE", 2018, office, f"Delaware 2018 {label}", candidates, "https://elections.delaware.gov/elections/resultsarchive/elect18/elect18_general/html/index.shtml", "delaware-semicolon-official", "B", district))
    return summary("Delaware", "DE", "Delaware Department of Elections official 2018 general results", "https://elections.delaware.gov/elections/resultsarchive/elect18/elect18_general/html/index.shtml", [{"election": {"state": "Delaware", "state_po": "DE", "year": 2018, "name": "Delaware 2018 General Election"}, "contests": contests}], "B")


def parse_illinois_2018() -> dict[str, Any]:
    path = ILLINOIS_DIR / "illinois_2018_2nd_congress.csv"
    totals: dict[tuple[str, str], int] = defaultdict(int)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            candidate = row["CandidateName"].strip()
            party = PARTIES.get(row["PartyName"].strip().upper(), row["PartyName"].strip().upper() or "OTHER")
            totals[(candidate, party)] += integer(row["VoteCount"])
    candidates = [{"candidate": candidate, "party": party, "votes": votes} for (candidate, party), votes in totals.items()]
    contest = contest_record("Illinois", "IL", 2018, "U.S. House", "Illinois 2018 2nd Congressional District", candidates, "https://www.elections.il.gov/PDFSiteMapProd.htm", "illinois-precinct-csv", "A", 2)
    return summary("Illinois", "IL", "Illinois State Board of Elections official 2018 general results", "https://www.elections.il.gov/PDFSiteMapProd.htm", [{"election": {"state": "Illinois", "state_po": "IL", "year": 2018, "name": "Illinois 2018 General Election"}, "contests": [contest]}], "A")


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT_DIR)}")


def main() -> int:
    idaho_elections = [parse_idaho(year)["elections"][0] for year in (2014, 2016, 2018)]
    write(ROOT_DIR / "public/results/idaho-legacy-2014-2018-summary.json", summary("Idaho", "ID", "Idaho Secretary of State official election archive", "https://archive.sos.idaho.gov/ELECT/results/index.html", idaho_elections, "B"))
    write(ROOT_DIR / "public/results/delaware-legacy-2018-summary.json", parse_delaware_2018())
    write(ROOT_DIR / "public/results/illinois-legacy-2018-summary.json", parse_illinois_2018())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
