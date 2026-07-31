#!/usr/bin/env python3
"""Parse Kentucky official county recap PDFs into statewide contest totals."""

from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/kentucky"
OUTPUT_PATH = ROOT_DIR / "public/results/kentucky-statewide-summary.json"

PARTY_MAP = {"DEM": "DEMOCRAT", "REP": "REPUBLICAN", "LIB": "LIBERTARIAN", "IND": "INDEPENDENT", "KY": "OTHER", "KEN": "OTHER"}
PARTY_RE = re.compile(r"\s+(DEM|REP|LIB|IND|KY)\s+")
PREFIX_PARTY_RE = re.compile(r"^(DEM|REP|LIB|IND|KEN)\s+(.+?)\s+(\d[\d,]*)(?:\s+|$)")
TOTAL_RE = re.compile(r"(\d[\d,]*)\s+\d+(?:\.\d+)?%\s*$")


def office_for_heading(line: str) -> tuple[str, int | None, str] | None:
    value = re.sub(r"\s+", " ", line.strip()).upper()
    if "PRESIDENT" in value and "UNITED STATES" in value:
        return "President", None, "President"
    if "UNITED STATES SENATOR" in value:
        return "U.S. Senate", None, "U.S. Senate"
    match = re.search(r"(?:UNITED STATES|U\.S\.) REPRESENTATIVE.*?(\d+)(?:ST|ND|RD|TH).*?(?:CONGRESSIONAL|CD).*?DISTRICT", value)
    if match:
        district = int(match.group(1))
        return "U.S. House", district, f"{district} Congressional District"
    match = re.search(r"STATE SENATOR.*?(\d+)(?:ST|ND|RD|TH).*?SENATORIAL.*?DISTRICT", value)
    if match:
        district = int(match.group(1))
        return "State Senate", district, f"{district} State Senate District"
    match = re.search(r"STATE REPRESENTATIVE.*?(\d+)(?:ST|ND|RD|TH).*?REPRESENTATIVE.*?DISTRICT", value)
    if match:
        district = int(match.group(1))
        return "State House", district, f"{district} State House District"
    return None


def parse_file(path: Path) -> dict[tuple[str, int | None], dict[tuple[str, str], int]]:
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True, errors="replace").stdout
    totals: dict[tuple[str, int | None], dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
    current: tuple[str, int | None] | None = None
    pending: tuple[str, int | None] | None = None
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        heading = office_for_heading(line)
        upper = line.upper()
        if heading:
            pending = (heading[0], heading[1])
            if "VOTE FOR" in upper:
                current = pending
                pending = None
            else:
                current = None
            continue
        if pending and upper.startswith("VOTE FOR"):
            current = pending
            pending = None
            continue
        if "VOTE FOR" in upper and not upper.startswith("VOTE FOR"):
            current = None
            pending = None
            continue
        if current and upper.startswith(("UNITED STATES REPRESENTATIVE", "U.S. REPRESENTATIVE", "STATE SENATE", "STATE REPRESENTATIVE")):
            current = None
            pending = None
            continue
        heading_prefixes = (
            "JUDGE", "COUNTY", "COMMONWEALTH", "CIRCUIT", "CLERK", "CORONER", "SHERIFF",
            "ATTORNEY", "PROPERTY", "SCHOOL", "MAYOR", "CITY", "MAGISTRATE", "CONSTABLE",
        )
        if current and not re.search(r"\d", line) and (" - " in line or upper.startswith(heading_prefixes)):
            current = None
            continue
        if current and upper.startswith("WRITE-IN TOTALS"):
            total_match = TOTAL_RE.search(line)
            values = re.findall(r"\d[\d,]*", line)
            total_votes = int(total_match.group(1).replace(",", "")) if total_match else (int(values[0].replace(",", "")) if values else 0)
            totals[current][("Write-In Totals", "OTHER")] += total_votes
            continue
        if current is None or not line or line.startswith(("Cast Votes:", "Undervotes:", "Overvotes:")):
            continue
        prefix_match = PREFIX_PARTY_RE.match(line)
        party_match = PARTY_RE.search(f" {line} ")
        total_match = TOTAL_RE.search(line)
        if prefix_match:
            party = PARTY_MAP[prefix_match.group(1)]
            candidate = prefix_match.group(2).strip()
            total_votes = int(prefix_match.group(3).replace(",", ""))
        elif party_match and total_match:
            candidate = line[:party_match.start()].strip()
            party = PARTY_MAP[party_match.group(1)]
            total_votes = int(total_match.group(1).replace(",", ""))
        else:
            continue
        if not candidate or candidate.upper() in {"CHOICE", "PARTY"}:
            continue
        totals[current][(candidate, party)] += total_votes
    return totals


def build_summary() -> dict[str, Any]:
    elections = []
    for year in (2022, 2024):
        files = sorted(RAW_DIR.glob(f"{year}_*.pdf"))
        contest_totals: dict[tuple[str, int | None], dict[tuple[str, str], int]] = defaultdict(lambda: defaultdict(int))
        for path in files:
            for contest, candidates in parse_file(path).items():
                for candidate, votes in candidates.items():
                    contest_totals[contest][candidate] += votes
        contests = []
        for contest_id, ((office, district), candidates_by_key) in enumerate(sorted(contest_totals.items(), key=lambda item: (item[0][0], item[0][1] or 0)), start=1):
            candidates = [{"candidate": name, "party": party, "votes": votes} for (name, party), votes in candidates_by_key.items()]
            candidates.sort(key=lambda item: (-item["votes"], item["candidate"]))
            if not candidates:
                continue
            label = office if district is None else f"{district} {office} District"
            contest = {
                "contest_id": contest_id,
                "office": office,
                "name": f"Kentucky {year} {label}",
                "state": "Kentucky",
                "state_po": "KY",
                "year": year,
                "source_format": "ky-county-recap-pdf",
                "quality_grade": "B",
                "total_votes": sum(candidate["votes"] for candidate in candidates),
                "winner": candidates[0],
                "margin_votes": candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0,
                "candidates": candidates,
                "source_files": len(files),
            }
            if district is not None:
                contest["district_number"] = district
                contest["district_label"] = label
            contests.append(contest)
        elections.append({"election": {"state": "Kentucky", "state_po": "KY", "year": year}, "contests": contests})
    return {"source": {"name": "Kentucky State Board of Elections official county recap reports", "url": "https://elect.ky.gov/results/2020-2029/Pages/2024General-Recap-Sheets.aspx", "official": True, "quality_grade": "B", "completeness": "partial"}, "state_po": "KY", "elections": elections}


def main() -> int:
    summary = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT_DIR)} with {sum(len(e['contests']) for e in summary['elections'])} contests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
