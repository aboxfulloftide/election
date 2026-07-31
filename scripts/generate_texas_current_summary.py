#!/usr/bin/env python3
"""Generate Texas current statewide contest summaries from SOS public HTML."""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "public/results/texas-current-summary.json"
SOURCE_URL = "https://electionresults.sos.state.tx.us/results.html"


PARTY_BY_ELECTION_NAME = {
    "DEMOCRATIC": "DEMOCRAT",
    "REPUBLICAN": "REPUBLICAN",
}


@dataclass(frozen=True)
class ParsedContest:
    election_name: str
    updated_at: str | None
    race_name: str
    polling_reporting: str | None
    candidates: list[dict[str, Any]]


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value).replace("\xa0", " ").split())


def int_value(value: str) -> int:
    return int(clean_text(value).replace(",", ""))


def title_case_name(value: str) -> str:
    # SOS current pages emit candidate names in all caps.
    return clean_text(value).title().replace("(I)", "(I)")


def office_for_race(race_name: str) -> tuple[str, int | None, str | None]:
    normalized = clean_text(race_name).upper()
    if normalized == "U. S. SENATOR":
        return "U.S. Senate", None, None
    match = re.match(r"U\. S\. REPRESENTATIVE DISTRICT\s+(\d+)$", normalized)
    if match:
        district = int(match.group(1))
        return "U.S. House", district, f"{district} Congressional District"
    match = re.match(r"STATE SENATOR, DISTRICT\s+(\d+)$", normalized)
    if match:
        district = int(match.group(1))
        return "State Senate", district, f"{district} State Senate District"
    match = re.match(r"STATE REPRESENTATIVE DISTRICT\s+(\d+)$", normalized)
    if match:
        district = int(match.group(1))
        return "State House", district, f"{district} State House District"
    raise RuntimeError(f"Unsupported Texas current race name: {race_name}")


def party_for_election(election_name: str) -> str:
    upper = election_name.upper()
    for token, party in PARTY_BY_ELECTION_NAME.items():
        if token in upper:
            return party
    return "OTHER"


def parse_page_date(page_html: str) -> tuple[int, str]:
    match = re.search(r"Election Results - ([^<]+)", page_html)
    if not match:
        raise RuntimeError("Could not find Texas current election date")
    election_date = dt.datetime.strptime(clean_text(match.group(1)), "%A, %B %d, %Y").date()
    return election_date.year, election_date.isoformat()


class TexasCurrentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.contests: list[ParsedContest] = []
        self._current_election = ""
        self._current_updated_at: str | None = None
        self._current_race = ""
        self._current_polling: str | None = None
        self._current_candidates: list[dict[str, Any]] | None = None
        self._in_button = False
        self._in_race = False
        self._in_polling = False
        self._in_row = False
        self._in_cell = False
        self._parts: list[str] = []
        self._row: list[str] = []

    def _finish_contest(self) -> None:
        if self._current_election and self._current_race and self._current_candidates:
            self.contests.append(
                ParsedContest(
                    election_name=self._current_election,
                    updated_at=self._current_updated_at,
                    race_name=self._current_race,
                    polling_reporting=self._current_polling,
                    candidates=self._current_candidates,
                )
            )
        self._current_race = ""
        self._current_polling = None
        self._current_candidates = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        attributes = {key.lower(): value or "" for key, value in attrs}
        if lowered == "button":
            self._finish_contest()
            self._in_button = True
            self._parts = []
        elif lowered == "div" and attributes.get("class") == "election":
            self._finish_contest()
            self._in_race = True
            self._parts = []
        elif lowered == "div" and attributes.get("class") == "polling":
            self._in_polling = True
            self._parts = []
        elif lowered == "tr":
            self._in_row = True
            self._row = []
        elif self._in_row and lowered in {"td", "th"}:
            self._in_cell = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._in_button or self._in_race or self._in_polling or self._in_cell:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._in_button and lowered == "button":
            label = clean_text(" ".join(self._parts))
            updated_match = re.search(r"\((Updated .+)\)$", label)
            self._current_updated_at = updated_match.group(1) if updated_match else None
            self._current_election = re.sub(r"\s*\(Updated .+\)$", "", label).strip()
            self._in_button = False
        elif self._in_race and lowered == "div":
            self._current_race = clean_text(" ".join(self._parts))
            self._current_candidates = []
            self._in_race = False
        elif self._in_polling and lowered == "div":
            self._current_polling = clean_text(" ".join(self._parts))
            self._in_polling = False
        elif self._in_cell and lowered in {"td", "th"}:
            self._row.append(clean_text(" ".join(self._parts)))
            self._in_cell = False
        elif self._in_row and lowered == "tr":
            if self._current_candidates is not None and len(self._row) == 2 and self._row[0] != "Candidate":
                self._current_candidates.append({"candidate": self._row[0], "votes": int_value(self._row[1])})
            self._in_row = False

    def close(self) -> None:
        self._finish_contest()
        super().close()


def parse_current_results(page_html: str) -> list[ParsedContest]:
    parser = TexasCurrentParser()
    parser.feed(page_html)
    parser.close()
    return parser.contests


def is_target_race(race_name: str) -> bool:
    try:
        office_for_race(race_name)
    except RuntimeError:
        return False
    return True


def materialize_contest(parsed: ParsedContest, year: int, election_date: str, contest_id: int) -> dict[str, Any]:
    office, district_number, district_label = office_for_race(parsed.race_name)
    party = party_for_election(parsed.election_name)
    candidates = sorted(
        [
            {"candidate": title_case_name(candidate["candidate"]), "party": party, "votes": candidate["votes"]}
            for candidate in parsed.candidates
        ],
        key=lambda item: item["votes"],
        reverse=True,
    )
    total_votes = sum(candidate["votes"] for candidate in candidates)
    contest: dict[str, Any] = {
        "contest_id": contest_id,
        "office": office,
        "name": f"Texas {year} {district_label or office} {party.title()} Primary Runoff",
        "state": "Texas",
        "state_po": "TX",
        "year": year,
        "election_date": election_date,
        "election_stage": "primary_runoff",
        "source_election_name": parsed.election_name,
        "source_url": SOURCE_URL,
        "source_format": "current-results-html",
        "quality_grade": "B",
        "polling_reporting": parsed.polling_reporting,
        "total_votes": total_votes,
        "winner": candidates[0],
        "margin_votes": candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0,
        "candidates": candidates,
        "counties": [],
    }
    if district_number is not None:
        contest["district_number"] = district_number
        contest["district_label"] = district_label
    return contest


def build_summary(page_html: str) -> dict[str, Any]:
    year, election_date = parse_page_date(page_html)
    contests = [
        materialize_contest(contest, year, election_date, contest_id)
        for contest_id, contest in enumerate((contest for contest in parse_current_results(page_html) if is_target_race(contest.race_name)), start=1)
    ]
    return {
        "source": {
            "name": "Texas Secretary of State current election results",
            "url": SOURCE_URL,
            "official": True,
            "quality_grade": "B",
        },
        "election": {
            "state": "Texas",
            "state_po": "TX",
            "year": year,
            "election_date": election_date,
            "name": f"{year} Texas Primary Runoff Election",
        },
        "scope": "statewide_current",
        "geography": "statewide",
        "contests": contests,
    }


def main() -> None:
    summary = build_summary(fetch_html(SOURCE_URL))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(summary['contests'])} Texas current contests.")


if __name__ == "__main__":
    main()
