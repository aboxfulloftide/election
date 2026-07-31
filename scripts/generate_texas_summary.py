#!/usr/bin/env python3
"""Generate Texas contest summaries from official historical SOS pages."""

from __future__ import annotations

import datetime as dt
import csv
import html
import json
import re
import sys
import subprocess
import tempfile
import time
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

from texas_config import (
    COUNTY_PRESIDENTIAL_SUMMARY_PATH,
    OUTPUT_PATH,
    ROOT_DIR,
    SOURCE_PAGE_URL,
    TEXAS_CANVASS_PDF_ELECTIONS,
    TEXAS_HISTORICAL_ELECTIONS,
    TexasCanvassPdfElection,
    TexasHistoricalElection,
)


TARGET_OFFICE_PATTERNS = (
    "U. S. Senator",
    "Governor",
    "U. S. Representative District",
    "State Senator, District",
    "State Representative District",
)
PARTY_MAP = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LIB": "LIBERTARIAN",
    "GRN": "GREEN",
    "IND": "INDEPENDENT",
    "W-I": "WRITE-IN",
    "WRI": "WRITE-IN",
}
COUNTY_ALIASES = {
    "COLLINGSWOR": "COLLINGSWORTH",
    "LASALLE": "LA SALLE",
    "THROCKMORT": "THROCKMORTON",
}
PDF_TARGET_RE = re.compile(
    r"^(PRESIDENT/VICE-PRESIDENT|GOVERNOR|U\. S\. SENATOR|U\. S\. REPRESENTATIVE DISTRICT \d+|STATE SENATOR, DISTRICT \d+|STATE REPRESENTATIVE DISTRICT \d+)$"
)
PDF_NON_TARGET_TERMS = (
    "LIEUTENANT",
    "ATTORNEY",
    "COMPTROLLER",
    "COMMISSIONER",
    "RAILROAD",
    "JUSTICE",
    "JUDGE",
    "MEMBER, STATE BOARD",
    "STATE BOARD",
    "COURT",
    "CRIMINAL",
    "DISTRICT ATTORNEY",
    "PROPOSITION",
)
PDF_NUMBER_RE = re.compile(r"^\d[\d,]*$")


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60) as response:
                return response.read().decode("windows-1252", errors="replace")
        except Exception as exc:  # pragma: no cover - exercised only on transient network failures
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"Could not fetch {url}: {last_error}") from last_error


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value).replace("\xa0", " ").split())


def int_value(value: str) -> int:
    cleaned = clean_text(value).replace(",", "").replace("-", "").strip()
    return int(cleaned or "0")


def normalize_party(value: str) -> str:
    value = clean_text(value).upper()
    return PARTY_MAP.get(value, value or "OTHER")


def normalize_county_name(value: str) -> str:
    normalized = clean_text(value).upper()
    return COUNTY_ALIASES.get(normalized, normalized)


def is_valid_pdf_candidate_label(value: str) -> bool:
    label = clean_text(value)
    if not label or label == "County" or "Total Votes" in label:
        return False
    return not bool(re.fullmatch(r"[\d, ]+", label))


def parse_pdf_candidate_label(value: str) -> dict[str, str]:
    label = clean_text(value).replace('"', "")
    party = "OTHER"
    party_match = re.search(r"\[([A-Z-]+)\]", label)
    if party_match:
        party = normalize_party(party_match.group(1))
        label = clean_text(label[: party_match.start()] + label[party_match.end() :])
    label = label.replace("(I)", "").strip()
    return {"candidate": label, "party": party}


def pdf_office_for_race(race_name: str) -> tuple[str, int | None, str | None]:
    if race_name == "PRESIDENT/VICE-PRESIDENT":
        return "President", None, None
    if race_name == "U. S. SENATOR":
        return "U.S. Senate", None, None
    if race_name == "GOVERNOR":
        return "Governor", None, None
    return office_for_race(race_name.title().replace("U. S.", "U. S."))


def load_texas_counties() -> dict[str, dict[str, str]]:
    summary = json.loads(COUNTY_PRESIDENTIAL_SUMMARY_PATH.read_text(encoding="utf-8"))
    counties = {
        normalize_county_name(county["county_name"]): {"fips": county["fips"], "county_name": county["county_name"]}
        for county in summary["counties"]
        if county["state_po"] == "TX"
    }
    if len(counties) != 254:
        raise RuntimeError(f"Expected 254 Texas counties in county presidential summary, found {len(counties)}")
    return counties


@dataclass(frozen=True)
class PdfWord:
    text: str
    top: float
    left: float
    width: float

    @property
    def cx(self) -> float:
        return self.left + self.width / 2


@dataclass
class PdfContestAccumulator:
    name: str
    labels: list[str]
    rows: dict[str, dict[str, Any]]
    county_order: list[str]
    continuation_offset: int = 0
    last_labels: list[str] | None = None
    last_start: int = 0

    def label_start(self, labels: list[str], *, reset_continuation: bool) -> int:
        labels = [clean_text(label) for label in labels if is_valid_pdf_candidate_label(label)]
        if not labels and self.last_labels:
            return self.last_start
        if not labels:
            return 0
        if labels == self.last_labels:
            return self.last_start
        for index in range(max(0, len(self.labels) - len(labels) + 1)):
            if self.labels[index : index + len(labels)] == labels:
                self.last_labels = labels
                self.last_start = index
                return index
        start = len(self.labels)
        self.labels.extend(labels)
        self.last_labels = labels
        self.last_start = start
        if reset_continuation:
            self.continuation_offset = 0
        return start

    def add_votes(self, county_name: str, values: list[str], start: int, total: str | None) -> None:
        if county_name not in self.rows:
            self.rows[county_name] = {"votes": [0] * len(self.labels), "total_votes": None}
            self.county_order.append(county_name)
        while len(self.rows[county_name]["votes"]) < len(self.labels):
            self.rows[county_name]["votes"].append(0)
        for index, value in enumerate(values):
            if start + index < len(self.rows[county_name]["votes"]):
                self.rows[county_name]["votes"][start + index] = int_value(value)
        if total is not None:
            self.rows[county_name]["total_votes"] = int_value(total)


class OptionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.options: list[tuple[int, str]] = []
        self._value: int | None = None
        self._parts: list[str] = []

    def _finish_option(self) -> None:
        if self._value is not None:
            self.options.append((self._value, clean_text(" ".join(self._parts))))
            self._value = None
            self._parts = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "option":
            self._finish_option()
            attributes = {key.lower(): value or "" for key, value in attrs}
            value = attributes.get("value", "")
            self._value = int(value) if value.isdigit() else None
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._value is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "option":
            self._finish_option()

    def close(self) -> None:
        self._finish_option()
        super().close()


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._in_cell = False
        self._in_row = False
        self._cell_parts: list[str] = []
        self._row: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "tr":
            self._in_row = True
            self._row = []
        elif self._in_row and lowered in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._in_cell and lowered in {"td", "th"}:
            self._row.append(clean_text(" ".join(self._cell_parts)))
            self._in_cell = False
        elif self._in_row and lowered == "tr":
            if self._row:
                self.rows.append(self._row)
            self._in_row = False


def pdf_to_tsv_rows(path: str) -> dict[int, list[PdfWord]]:
    pdf_path = ROOT_DIR / path
    with tempfile.NamedTemporaryFile(suffix=".tsv") as tsv_file:
        subprocess.run(["pdftotext", "-tsv", str(pdf_path), tsv_file.name], check=True, timeout=120)
        tsv_file.seek(0)
        reader = csv.DictReader((line.decode("utf-8", errors="replace") for line in tsv_file), delimiter="\t")
        pages: dict[int, list[PdfWord]] = {}
        for row in reader:
            text = row.get("text", "").strip()
            if not text or text in {"###PAGE###", "###FLOW###", "###LINE###"}:
                continue
            try:
                page = int(row["page_num"])
                word = PdfWord(text=text, top=float(row["top"]), left=float(row["left"]), width=float(row["width"]))
            except (KeyError, ValueError):
                continue
            pages.setdefault(page, []).append(word)
    return pages


def group_pdf_lines(words: list[PdfWord]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for word in sorted(words, key=lambda item: (item.top, item.left)):
        for line in lines:
            if abs(float(line["top"]) - word.top) < 3:
                line["words"].append(word)
                line["top"] = (float(line["top"]) * (len(line["words"]) - 1) + word.top) / len(line["words"])
                break
        else:
            lines.append({"top": word.top, "words": [word]})
    for line in lines:
        line["words"].sort(key=lambda item: item.left)
        line["text"] = clean_text(" ".join(word.text for word in line["words"]))
    return lines


def is_pdf_noise_line(text: str) -> bool:
    return (
        not text
        or text == "County"
        or text.startswith("Texas Secretary")
        or text.startswith("County by County Canvass")
        or text.startswith("202")
        or text.startswith("November ")
        or text.startswith("Page ")
        or bool(re.match(r"^\d+$", text))
        or bool(re.match(r"^\d{2}/\d{2}/\d{4}", text))
    )


def is_pdf_non_target_heading(text: str, top: float) -> bool:
    if not 120 <= top <= 145:
        return False
    if PDF_TARGET_RE.match(text):
        return False
    return any(term in text for term in PDF_NON_TARGET_TERMS)


def pdf_county_prefix(words: list[PdfWord], county_names: set[str]) -> str | None:
    parts = []
    for word in words:
        if PDF_NUMBER_RE.match(word.text):
            break
        parts.append(word.text)
    name = normalize_county_name(" ".join(parts))
    return name if name in county_names else None


def pdf_row_kind(line: dict[str, Any], county_names: set[str]) -> tuple[str, str | None, list[PdfWord]] | None:
    words: list[PdfWord] = line["words"]
    numbers = [word for word in words if PDF_NUMBER_RE.match(word.text)]
    if not numbers:
        return None
    text = str(line["text"])
    if text.startswith("TOTAL VOTES"):
        return ("total", None, numbers)
    county_name = pdf_county_prefix(words, county_names)
    if county_name:
        return ("county", county_name, numbers)
    if PDF_NUMBER_RE.match(words[0].text):
        return ("continuation", None, numbers)
    return None


def pdf_labels_for_chunk(header_lines: list[dict[str, Any]], value_columns: list[PdfWord]) -> list[str]:
    header_words = [word for line in header_lines for word in line["words"]]
    centers = [word.cx for word in value_columns]
    labels = []
    for index, center in enumerate(centers):
        left = (centers[index - 1] + center) / 2 if index else center - 70
        right = (center + centers[index + 1]) / 2 if index + 1 < len(centers) else center + 90
        words = [word for word in header_words if left <= word.cx < right and word.text != "County"]
        labels.append(clean_text(" ".join(word.text for word in sorted(words, key=lambda item: (item.top, item.left)))))
    return labels


def split_pdf_values(labels: list[str], value_words: list[PdfWord], previous_vote_label_count: int) -> tuple[list[str], list[str], str | None]:
    total_index = next((index for index, label in enumerate(labels) if "Total Votes" in label), None)
    values = [word.text for word in value_words]
    if total_index is None and previous_vote_label_count and len(values) > previous_vote_label_count:
        total_index = previous_vote_label_count
    if total_index is None:
        return labels, values, None
    return labels[:total_index], values[:total_index], values[total_index] if len(values) > total_index else None


def parse_pdf_contests(election: TexasCanvassPdfElection, county_lookup: dict[str, dict[str, str]]) -> list[PdfContestAccumulator]:
    county_names = set(county_lookup)
    pages = pdf_to_tsv_rows(election.raw_path)
    current_contest: str | None = None
    contests: dict[str, PdfContestAccumulator] = {}
    for page_number in sorted(pages):
        lines = group_pdf_lines(pages[page_number])
        for line in lines:
            text = str(line["text"])
            if PDF_TARGET_RE.match(text):
                current_contest = text
                contests.setdefault(text, PdfContestAccumulator(text, [], {}, []))
                break
            if is_pdf_non_target_heading(text, float(line["top"])):
                current_contest = None
                break
        if current_contest is None:
            continue
        contest = contests[current_contest]
        header_lines: list[dict[str, Any]] = []
        data_rows: list[tuple[str, str | None, list[PdfWord]]] = []

        def flush_rows() -> None:
            nonlocal header_lines, data_rows
            if not data_rows:
                header_lines = []
                return
            labels = pdf_labels_for_chunk(header_lines, data_rows[0][2])
            previous_count = len(contest.last_labels or [])
            vote_labels, _, _ = split_pdf_values(labels, data_rows[0][2], previous_count)
            use_previous = not any(is_valid_pdf_candidate_label(label) for label in vote_labels) and contest.last_labels
            if use_previous:
                start = contest.last_start
                vote_label_count = len(contest.last_labels or [])
            else:
                start = contest.label_start(vote_labels, reset_continuation=not any(kind == "county" for kind, _, _ in data_rows))
                vote_label_count = len(contest.last_labels or vote_labels)
            for kind, county_name, numbers in data_rows:
                labels_for_split = list(contest.last_labels or []) + ["Total Votes"] if use_previous else labels
                _, values, total = split_pdf_values(labels_for_split, numbers, vote_label_count)
                if kind == "county" and county_name:
                    contest.add_votes(county_name, values, start, total)
                elif kind == "continuation" and contest.continuation_offset < len(contest.county_order):
                    contest.add_votes(contest.county_order[contest.continuation_offset], values, start, total)
                    contest.continuation_offset += 1
            header_lines = []
            data_rows = []

        for line in lines:
            text = str(line["text"])
            if PDF_TARGET_RE.match(text):
                header_lines = []
                data_rows = []
                continue
            if is_pdf_noise_line(text):
                continue
            row = pdf_row_kind(line, county_names)
            if row:
                data_rows.append(row)
                if row[0] == "total":
                    flush_rows()
                continue
            if data_rows:
                flush_rows()
            header_lines.append(line)
        flush_rows()
    return list(contests.values())


def parse_race_options(page_html: str) -> list[tuple[int, str]]:
    parser = OptionParser()
    parser.feed(page_html)
    parser.close()
    return [(race_id, race_name) for race_id, race_name in parser.options if race_name.startswith(TARGET_OFFICE_PATTERNS)]


def office_for_race(race_name: str) -> tuple[str, int | None, str | None]:
    if race_name == "U. S. Senator":
        return "U.S. Senate", None, None
    if race_name == "Governor":
        return "Governor", None, None
    match = re.search(r"U\. S\. Representative District\s+(\d+)", race_name)
    if match:
        district = int(match.group(1))
        return "U.S. House", district, f"{district} Congressional District"
    match = re.search(r"State Senator, District\s+(\d+)", race_name)
    if match:
        district = int(match.group(1))
        return "State Senate", district, f"{district} State Senate District"
    match = re.search(r"State Representative District\s+(\d+)", race_name)
    if match:
        district = int(match.group(1))
        return "State House", district, f"{district} State House District"
    raise RuntimeError(f"Unsupported Texas race name: {race_name}")


def parse_race_page(page_html: str) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    parser = TableParser()
    parser.feed(page_html)
    if len(parser.rows) < 4:
        raise RuntimeError("Texas race page did not contain expected table rows")
    candidate_names = parser.rows[0][1:]
    party_row = parser.rows[2]
    try:
        total_column = party_row.index("Votes")
    except ValueError as exc:
        raise RuntimeError(f"Could not find total Votes column in Texas race page header: {party_row}") from exc
    candidate_count = total_column - 1
    candidates = [
        {"candidate": candidate_names[index], "party": normalize_party(party_row[index + 1])}
        for index in range(candidate_count)
        if candidate_names[index]
    ]
    counties = []
    for row in parser.rows[3:]:
        if len(row) < total_column + 1:
            continue
        county_name = normalize_county_name(row[0])
        if county_name == "ALL COUNTIES":
            continue
        votes = [int_value(row[index + 1]) for index in range(len(candidates))]
        counties.append({"county_name": county_name, "candidate_votes": votes, "total_votes": int_value(row[total_column])})
    return candidates, counties


def materialize_candidates(candidates: list[dict[str, str]], votes: list[int]) -> list[dict[str, Any]]:
    return sorted(
        [
            {"candidate": candidate["candidate"], "party": candidate["party"], "votes": vote}
            for candidate, vote in zip(candidates, votes)
        ],
        key=lambda item: item["votes"],
        reverse=True,
    )


def build_contest(
    election: TexasHistoricalElection,
    race_id: int,
    race_name: str,
    candidates: list[dict[str, str]],
    county_rows: list[dict[str, Any]],
    county_lookup: dict[str, dict[str, str]],
    contest_id: int,
) -> dict[str, Any]:
    office, district_number, district_label = office_for_race(race_name)
    statewide_votes = [0] * len(candidates)
    counties = []
    for row in county_rows:
        county_info = county_lookup.get(row["county_name"])
        if county_info is None:
            raise RuntimeError(f"Unknown Texas county: {row['county_name']}")
        county_candidates = materialize_candidates(candidates, row["candidate_votes"])
        county_total = sum(candidate["votes"] for candidate in county_candidates)
        if county_total != row["total_votes"]:
            raise RuntimeError(f"County total mismatch for {race_name} in {row['county_name']}: {county_total} != {row['total_votes']}")
        for index, votes in enumerate(row["candidate_votes"]):
            statewide_votes[index] += votes
        counties.append(
            {
                "fips": county_info["fips"],
                "county_name": county_info["county_name"],
                "total_votes": county_total,
                "winner": county_candidates[0],
                "margin_votes": county_candidates[0]["votes"] - county_candidates[1]["votes"] if len(county_candidates) > 1 else 0,
                "candidates": county_candidates,
            }
        )
    contest_candidates = materialize_candidates(candidates, statewide_votes)
    total_votes = sum(candidate["votes"] for candidate in contest_candidates)
    contest = {
        "contest_id": contest_id,
        "office": office,
        "name": f"Texas {election.year} {district_label or office}",
        "state": "Texas",
        "state_po": "TX",
        "total_votes": total_votes,
        "winner": contest_candidates[0],
        "margin_votes": contest_candidates[0]["votes"] - contest_candidates[1]["votes"] if len(contest_candidates) > 1 else 0,
        "candidates": contest_candidates,
        "counties": sorted(counties, key=lambda item: item["fips"]),
        "source_url": election.race_url(race_id),
        "source_race_id": str(race_id),
        "quality_grade": "A",
    }
    if district_number is not None:
        contest["district_number"] = district_number
        contest["district_label"] = district_label
    return contest


def build_pdf_contest(
    election: TexasCanvassPdfElection,
    parsed: PdfContestAccumulator,
    county_lookup: dict[str, dict[str, str]],
    contest_id: int,
) -> dict[str, Any] | None:
    labels = [label for label in parsed.labels if is_valid_pdf_candidate_label(label)]
    if not labels:
        return None
    candidates = [parse_pdf_candidate_label(label) for label in labels]
    office, district_number, district_label = pdf_office_for_race(parsed.name)
    statewide_votes = [0] * len(candidates)
    counties = []
    for county_name, row in parsed.rows.items():
        votes = list(row["votes"][: len(candidates)])
        while len(votes) < len(candidates):
            votes.append(0)
        total_votes = row["total_votes"] if row["total_votes"] is not None else sum(votes)
        if total_votes == 0:
            continue
        if sum(votes) != total_votes:
            raise RuntimeError(f"Texas PDF county total mismatch for {parsed.name} in {county_name}: {sum(votes)} != {total_votes}")
        county_info = county_lookup[county_name]
        county_candidates = materialize_candidates(candidates, votes)
        counties.append(
            {
                "fips": county_info["fips"],
                "county_name": county_info["county_name"],
                "total_votes": total_votes,
                "winner": county_candidates[0],
                "margin_votes": county_candidates[0]["votes"] - county_candidates[1]["votes"] if len(county_candidates) > 1 else 0,
                "candidates": county_candidates,
            }
        )
        for index, vote in enumerate(votes):
            statewide_votes[index] += vote
    if not counties:
        return None
    contest_candidates = materialize_candidates(candidates, statewide_votes)
    total_votes = sum(candidate["votes"] for candidate in contest_candidates)
    contest: dict[str, Any] = {
        "contest_id": contest_id,
        "office": office,
        "name": f"Texas {election.year} {district_label or office}",
        "state": "Texas",
        "state_po": "TX",
        "year": election.year,
        "election_date": election.election_date,
        "source_election_name": election.election_name,
        "source_url": election.source_url,
        "source_format": "texas-county-canvass-pdf",
        "quality_grade": "B",
        "total_votes": total_votes,
        "winner": contest_candidates[0],
        "margin_votes": contest_candidates[0]["votes"] - contest_candidates[1]["votes"] if len(contest_candidates) > 1 else 0,
        "candidates": contest_candidates,
        "counties": sorted(counties, key=lambda item: item["fips"]),
    }
    if district_number is not None:
        contest["district_number"] = district_number
        contest["district_label"] = district_label
    return contest


def build_pdf_election(election: TexasCanvassPdfElection) -> dict[str, Any]:
    county_lookup = load_texas_counties()
    contests = []
    for parsed in parse_pdf_contests(election, county_lookup):
        contest = build_pdf_contest(election, parsed, county_lookup, len(contests) + 1)
        if contest is not None:
            contests.append(contest)
    return {
        "source": {
            "name": "Texas Secretary of State County by County Canvass Report",
            "url": election.source_url,
            "homepage": SOURCE_PAGE_URL,
            "quality_grade": "B",
        },
        "election": {
            "year": election.year,
            "date": election.election_date,
            "type": "general",
            "state": "Texas",
            "state_po": "TX",
            "name": election.election_name,
        },
        "contests": contests,
    }


def build_election(election: TexasHistoricalElection) -> dict[str, Any]:
    county_lookup = load_texas_counties()
    race_options = parse_race_options(fetch_html(election.race_select_url))
    contests = []
    for contest_id, (race_id, race_name) in enumerate(race_options, start=1):
        candidates, county_rows = parse_race_page(fetch_html(election.race_url(race_id)))
        contests.append(build_contest(election, race_id, race_name, candidates, county_rows, county_lookup, contest_id))
    return {
        "source": {
            "name": "Texas Secretary of State historical election results",
            "url": election.race_select_url,
            "homepage": SOURCE_PAGE_URL,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": "A",
        },
        "election": {
            "year": election.year,
            "date": election.election_date,
            "type": "general",
            "state": "Texas",
            "state_po": "TX",
            "source_election_id": election.election_id,
            "name": election.election_name,
        },
        "contests": contests,
    }


def build_summary() -> dict[str, Any]:
    return {
        "source": {
            "name": "Texas Secretary of State historical election results",
            "url": SOURCE_PAGE_URL,
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "quality_grade": "A",
        },
        "elections": [build_election(election) for election in TEXAS_HISTORICAL_ELECTIONS]
        + [build_pdf_election(election) for election in TEXAS_CANVASS_PDF_ELECTIONS],
    }


def main() -> int:
    summary = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    contest_count = sum(len(election["contests"]) for election in summary["elections"])
    print(f"Wrote {OUTPUT_PATH.relative_to(OUTPUT_PATH.parents[2])} with {contest_count} Texas contests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
