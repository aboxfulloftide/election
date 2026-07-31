#!/usr/bin/env python3
"""Generate Florida municipal mayor summaries from official ENR pages."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.request import Request, urlopen

from florida_mayor_config import MAYOR_SOURCES, OUTPUT_PATH, FloridaMayorSource


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def int_value(value: str) -> int:
    cleaned = value.replace(",", "").strip()
    if cleaned == "-":
        return 0
    if not cleaned.isdigit():
        raise RuntimeError(f"Could not parse vote value {value!r}")
    return int(cleaned)


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def place_from_race_name(race_name: str, default_place: str | None = None) -> str:
    normalized = clean_text(race_name)
    lowered = normalized.lower()
    if lowered.startswith("miabch"):
        return "Miami Beach"
    if lowered == "mayor" and default_place:
        return default_place
    if "mayor" not in lowered:
        return normalized
    place = clean_text(normalized[: lowered.index("mayor")].strip(" -"))
    return place or default_place or normalized


class EnrSummaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.races: list[dict[str, Any]] = []
        self._race: dict[str, Any] | None = None
        self._race_div_depth = 0
        self._race_name_depth = 0
        self._in_detail_table = False
        self._in_tbody = False
        self._in_tr = False
        self._in_td = False
        self._capture_label = False
        self._cell_parts: list[str] = []
        self._row: list[str] = []
        self._label_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        classes = attributes.get("class", "")
        if tag == "div" and self._race is None and "Race" in classes.split() and "row" in classes.split():
            self._race = {"source_race_id": attributes.get("id", ""), "race_name": "", "rows": []}
            self._race_div_depth = 1
            return

        if self._race is not None and tag == "div":
            self._race_div_depth += 1
            if "RaceName" in classes.split():
                self._race_name_depth = 1
                return
            if self._race_name_depth:
                self._race_name_depth += 1

        if self._race is not None and self._race_name_depth and tag == "label":
            self._capture_label = True
            self._label_parts = []

        if self._race is not None and tag == "table" and "DetailResults" in classes.split():
            self._in_detail_table = True
        elif self._in_detail_table and tag == "tbody":
            self._in_tbody = True
        elif self._in_tbody and tag == "tr":
            self._in_tr = True
            self._row = []
        elif self._in_tr and tag == "td":
            self._in_td = True
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture_label:
            self._label_parts.append(data)
        if self._in_td:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._capture_label and tag == "label":
            label = clean_text(" ".join(self._label_parts))
            if label and self._race is not None:
                self._race["race_name"] = label
            self._capture_label = False

        if self._in_td and tag == "td":
            self._row.append(clean_text(" ".join(self._cell_parts)))
            self._in_td = False
        elif self._in_tr and tag == "tr":
            if self._race is not None and len(self._row) >= 3:
                self._race["rows"].append(self._row)
            self._in_tr = False
        elif self._in_tbody and tag == "tbody":
            self._in_tbody = False
        elif self._in_detail_table and tag == "table":
            self._in_detail_table = False

        if self._race is not None and tag == "div":
            if self._race_name_depth:
                self._race_name_depth -= 1
            self._race_div_depth -= 1
            if self._race_div_depth == 0:
                self.races.append(self._race)
                self._race = None


def parse_mayor_races(page_html: str) -> list[dict[str, Any]]:
    parser = EnrSummaryParser()
    parser.feed(page_html)
    return [
        race
        for race in parser.races
        if re.search(r"\bmayor\b", race["race_name"], flags=re.IGNORECASE) and not is_yes_no_question(race)
    ]


def is_yes_no_question(race: dict[str, Any]) -> bool:
    choices = {clean_text(row[0]).casefold() for row in race["rows"] if row}
    return bool(choices) and choices <= {"yes", "no", "yes - for bonds", "no - against bonds"}


PARTY_SUFFIXES = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "NPA": "NONPARTISAN",
    "NON": "NONPARTISAN",
}


def candidate_from_cell(raw_name: str) -> dict[str, Any]:
    name = clean_text(raw_name)
    party = "NONPARTISAN"
    suffix_match = re.search(r"\s+\(([A-Z]{3})\)$", name, flags=re.IGNORECASE)
    if suffix_match:
        suffix = suffix_match.group(1).upper()
        party = PARTY_SUFFIXES.get(suffix, suffix)
        name = clean_text(name[: suffix_match.start()])
    return {"candidate": name, "party": party}


def build_contest(source: FloridaMayorSource, race: dict[str, Any], contest_id: int) -> dict[str, Any]:
    candidates = []
    for row in race["rows"]:
        if row and row[0]:
            candidate = candidate_from_cell(row[0])
            candidate["votes"] = int_value(row[-2])
            candidates.append(candidate)
    if not candidates:
        raise RuntimeError(f"No candidates parsed for {race['race_name']} from {source.url}")
    candidates.sort(key=lambda item: item["votes"], reverse=True)
    total_votes = sum(candidate["votes"] for candidate in candidates)
    margin_votes = candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0
    place = place_from_race_name(race["race_name"], source.default_place)
    return {
        "contest_id": contest_id,
        "state": "Florida",
        "state_po": "FL",
        "county": source.county,
        "county_fips": source.county_fips,
        "place": place,
        "office": "Mayor",
        "election_stage": "runoff" if "runoff" in source.election_name.lower() or "run-off" in source.election_name.lower() else "general",
        "election_date": source.election_date,
        "year": source.year,
        "name": f"{place} {source.year} Mayor",
        "source_race_id": race["source_race_id"],
        "source_url": source.url,
        "total_votes": total_votes,
        "winner": candidates[0],
        "margin_votes": margin_votes,
        "candidates": candidates,
    }


def build_summary() -> dict[str, Any]:
    elections = []
    contest_id = 1
    for source in MAYOR_SOURCES:
        contests = []
        for race in parse_mayor_races(fetch_html(source.url)):
            contests.append(build_contest(source, race, contest_id))
            contest_id += 1
        elections.append(
            {
                "election": {
                    "year": source.year,
                    "date": source.election_date,
                    "name": source.election_name,
                    "state": "Florida",
                    "state_po": "FL",
                    "county": source.county,
                    "county_fips": source.county_fips,
                },
                "source": {
                    "name": source.source_name,
                    "url": source.url,
                    "homepage": source.homepage,
                    "official": True,
                    "quality_grade": "A",
                },
                "contests": contests,
            }
        )
    return {
        "source": {
            "name": "Florida county Supervisor of Elections Election Night Reporting pages",
            "url": "https://enr.electionsfl.org/",
            "official": True,
            "quality_grade": "A",
        },
        "state_po": "FL",
        "scope": "municipal_mayors",
        "elections": elections,
    }


def main() -> None:
    summary = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    contest_count = sum(len(election["contests"]) for election in summary["elections"])
    print(f"Wrote {OUTPUT_PATH} with {contest_count} Florida mayor contests.")


if __name__ == "__main__":
    main()
