#!/usr/bin/env python3
"""Generate Texas municipal mayor summaries from official city pages."""

from __future__ import annotations

import datetime as dt
import csv
import hashlib
import html
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from texas_mayor_config import MAYOR_SOURCES, OUTPUT_PATH, TexasMayorElectionFile, TexasMayorSource


ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT_DIR / "data/raw/official/texas/mayors"


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        return subprocess.check_output(
            ["curl", "-L", "--fail", "--silent", "--show-error", url],
            timeout=60,
        ).decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except Exception:
        return subprocess.check_output(["curl", "-L", "--fail", "--silent", "--show-error", url], timeout=60)


def cache_stem(url: str) -> str:
    parsed = urlparse(url)
    basename = Path(unquote(parsed.path)).name or "source"
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", basename).strip("-") or "source"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{digest}-{safe_name}"


def read_or_write_cache(path: Path, builder: Any, *, binary: bool = False) -> Any:
    if path.exists():
        return path.read_bytes() if binary else path.read_text(encoding="utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    value = builder()
    if binary:
        path.write_bytes(value)
    else:
        path.write_text(value, encoding="utf-8")
    return value


def cached_fetch_bytes(url: str) -> bytes:
    return read_or_write_cache(CACHE_DIR / "downloads" / cache_stem(url), lambda: fetch_bytes(url), binary=True)


def pdf_to_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file, tempfile.NamedTemporaryFile(suffix=".txt") as text_file:
        pdf_file.write(data)
        pdf_file.flush()
        subprocess.run(["pdftotext", "-layout", pdf_file.name, text_file.name], check=True, timeout=60)
        text_file.seek(0)
        return text_file.read().decode("utf-8", errors="replace")


def cached_pdf_to_text(election_file: TexasMayorElectionFile) -> str:
    text_path = CACHE_DIR / "text" / f"{cache_stem(election_file.url)}.txt"
    return read_or_write_cache(text_path, lambda: pdf_to_text(cached_fetch_bytes(election_file.url)))


def pdf_to_ocr_text(data: bytes) -> str:
    with (
        tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file,
        tempfile.NamedTemporaryFile(suffix=".pdf") as ocr_file,
        tempfile.NamedTemporaryFile(suffix=".txt") as text_file,
    ):
        pdf_file.write(data)
        pdf_file.flush()
        subprocess.run(
            ["ocrmypdf", "--force-ocr", "--jobs", "2", "--output-type", "pdf", pdf_file.name, ocr_file.name],
            check=True,
            timeout=180,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(["pdftotext", "-layout", ocr_file.name, text_file.name], check=True, timeout=60)
        text_file.seek(0)
        return text_file.read().decode("utf-8", errors="replace")


def cached_pdf_to_ocr_text(election_file: TexasMayorElectionFile) -> str:
    text_path = CACHE_DIR / "ocr-text" / f"{cache_stem(election_file.url)}.txt"
    return read_or_write_cache(text_path, lambda: pdf_to_ocr_text(cached_fetch_bytes(election_file.url)))


def decode_source_text(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    if "\ufffd" in text:
        return data.decode("windows-1252", errors="replace")
    return text


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value).replace("\xa0", " ").split())


def int_value(value: str) -> int:
    cleaned = clean_text(value).replace(",", "").strip()
    if not cleaned:
        return 0
    if not cleaned.isdigit():
        raise RuntimeError(f"Could not parse vote value {value!r}")
    return int(cleaned)


def int_value_with_ocr_digits(value: str) -> int:
    return int_value(value.translate(str.maketrans({"I": "1", "i": "1", "l": "1", "|": "1", "r": "1"})))


def normalize_candidate_name(value: str) -> str:
    normalized = clean_text(value)
    if len(normalized) > 2 and normalized.endswith("."):
        normalized = normalized[:-1]
    if normalized.casefold() == "gina ortiz jones":
        return "Gina Ortiz Jones"
    if "dutrow" in normalized.casefold() and "nthony" in normalized.casefold():
        return "ANTHONY M. DUTROW"
    if normalized == "ANTHONY M . DUTROW":
        return "ANTHONY M. DUTROW"
    if normalized == "E. Edward Okpa IT":
        return "E. Edward Okpa II"
    if normalized.casefold() == "michael jdrogo":
        return "Michael Idrogo"
    return normalized


@dataclass(frozen=True)
class ElectionHeading:
    name: str
    source_url: str


@dataclass(frozen=True)
class TableBlock:
    heading: ElectionHeading
    previous_text: str
    rows: list[list[str]]


class ElectionHistoryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[TableBlock] = []
        self._latest_heading: ElectionHeading | None = None
        self._last_paragraph = ""
        self._in_heading = False
        self._heading_parts: list[str] = []
        self._heading_href = ""
        self._in_paragraph = False
        self._paragraph_parts: list[str] = []
        self._in_table = False
        self._table_previous_text = ""
        self._rows: list[list[str]] = []
        self._in_row = False
        self._row: list[str] = []
        self._in_cell = False
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        attributes = {key.lower(): value or "" for key, value in attrs}
        if lowered in {"h3", "h4"}:
            self._in_heading = True
            self._heading_parts = []
            self._heading_href = ""
        elif self._in_heading and lowered == "a":
            self._heading_href = attributes.get("href", "")
        elif lowered == "p":
            self._in_paragraph = True
            self._paragraph_parts = []
        elif lowered == "table":
            self._in_table = True
            self._table_previous_text = self._last_paragraph
            self._rows = []
        elif self._in_table and lowered == "tr":
            self._in_row = True
            self._row = []
        elif self._in_row and lowered in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_parts.append(data)
        if self._in_paragraph:
            self._paragraph_parts.append(data)
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._in_cell and lowered in {"td", "th"}:
            self._row.append(clean_text(" ".join(self._cell_parts)))
            self._in_cell = False
        elif self._in_row and lowered == "tr":
            if any(cell for cell in self._row):
                self._rows.append(self._row)
            self._in_row = False
        elif self._in_table and lowered == "table":
            if self._latest_heading and self._rows:
                self.tables.append(TableBlock(self._latest_heading, self._table_previous_text, self._rows))
            self._in_table = False
        elif self._in_paragraph and lowered == "p":
            paragraph = clean_text(" ".join(self._paragraph_parts))
            if paragraph:
                self._last_paragraph = paragraph
            self._in_paragraph = False
        elif self._in_heading and lowered in {"h3", "h4"}:
            heading = clean_text(" ".join(self._heading_parts))
            if re.search(r"\b(?:General|Runoff) Election\b", heading, flags=re.IGNORECASE):
                self._latest_heading = ElectionHeading(heading, html.unescape(self._heading_href))
            self._in_heading = False


def parse_tables(page_html: str) -> list[TableBlock]:
    parser = ElectionHistoryParser()
    parser.feed(page_html)
    return parser.tables


def parse_heading(heading: ElectionHeading) -> tuple[int, str, str, str]:
    match = re.search(r"\b(General|Runoff) Election,\s+([A-Za-z]+ \d{1,2}, \d{4})", heading.name)
    if not match:
        raise RuntimeError(f"Unsupported Fort Worth election heading: {heading.name}")
    election_date = dt.datetime.strptime(match.group(2), "%B %d, %Y").date()
    stage = match.group(1).lower()
    return election_date.year, election_date.isoformat(), stage, heading.name


def is_mayor_table(block: TableBlock) -> bool:
    if clean_text(block.previous_text).casefold() == "mayor":
        return True
    return bool(block.rows and block.rows[0] and clean_text(block.rows[0][0]).casefold() == "mayor")


def vote_total_index(header: list[str]) -> int:
    for index, cell in enumerate(header):
        if clean_text(cell).casefold().replace(" ", "") in {"votetotal", "votetotal"}:
            return index
    raise RuntimeError(f"Mayor table header has no Vote Total column: {header}")


def parse_mayor_rows(block: TableBlock) -> list[dict[str, Any]]:
    if not is_mayor_table(block):
        return []
    header_index = next((index for index, row in enumerate(block.rows) if row and clean_text(row[0]).casefold() == "candidate"), None)
    if header_index is None:
        return []
    header = block.rows[header_index]
    total_index = vote_total_index(header)
    county_columns = [(index, clean_text(cell)) for index, cell in enumerate(header) if index not in {0, total_index} and "county" in cell.lower()]
    candidates = []
    for row in block.rows[header_index + 1 :]:
        if not row or not row[0]:
            continue
        first_cell = clean_text(row[0])
        if re.match(r"^(District|Proposition)\b", first_cell, flags=re.IGNORECASE):
            break
        if len(row) <= total_index:
            continue
        votes = int_value(row[total_index])
        county_votes = {
            county_name: int_value(row[index]) if index < len(row) else 0
            for index, county_name in county_columns
            if county_name
        }
        candidates.append({"candidate": first_cell, "party": "NONPARTISAN", "votes": votes, "county_votes": county_votes})
    return sorted(candidates, key=lambda item: item["votes"], reverse=True)


def build_contest(source: TexasMayorSource, block: TableBlock, contest_id: int) -> dict[str, Any] | None:
    candidates = parse_mayor_rows(block)
    if not candidates:
        return None
    year, election_date, election_stage, election_name = parse_heading(block.heading)
    total_votes = sum(candidate["votes"] for candidate in candidates)
    margin_votes = candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0
    return {
        "contest_id": contest_id,
        "state": "Texas",
        "state_po": "TX",
        "place": source.place,
        "office": "Mayor",
        "election_stage": election_stage,
        "election_date": election_date,
        "year": year,
        "name": f"{source.place} {year} Mayor",
        "source_election_name": election_name,
        "source_url": block.heading.source_url or source.url,
        "total_votes": total_votes,
        "winner": candidates[0],
        "margin_votes": margin_votes,
        "county_portions": [
            {"county_name": county_name, "fips": fips}
            for county_name, fips in source.county_portion_fips.items()
            if any(candidate["county_votes"].get(county_name, 0) for candidate in candidates)
        ],
        "candidates": candidates,
    }


def materialize_mayor_contest(
    source: TexasMayorSource,
    election_file: TexasMayorElectionFile,
    candidates: list[dict[str, Any]],
    contest_id: int,
) -> dict[str, Any]:
    candidates = sorted(candidates, key=lambda item: item["votes"], reverse=True)
    total_votes = sum(candidate["votes"] for candidate in candidates)
    margin_votes = candidates[0]["votes"] - candidates[1]["votes"] if len(candidates) > 1 else 0
    county_portion_fips = election_file.county_portion_fips or source.county_portion_fips
    return {
        "contest_id": contest_id,
        "state": "Texas",
        "state_po": "TX",
        "place": source.place,
        "office": "Mayor",
        "election_stage": election_file.election_stage,
        "election_date": election_file.election_date,
        "year": election_file.year,
        "name": f"{source.place} {election_file.year} Mayor",
        "source_election_name": election_file.election_name,
        "source_url": election_file.url,
        "source_format": election_file.format,
        "quality_grade": election_file.quality_grade,
        "total_votes": total_votes,
        "winner": candidates[0],
        "margin_votes": margin_votes,
        "county_portions": [{"county_name": county_name, "fips": fips} for county_name, fips in county_portion_fips.items()],
        "candidates": candidates,
    }


def parse_electionware_mayor_csv(csv_text: str) -> list[dict[str, Any]]:
    from collections import Counter

    votes: Counter[str] = Counter()
    in_mayor_section = False
    for row in csv.reader(csv_text.splitlines()):
        cells = [clean_text(cell) for cell in row]
        row_text = " ".join(cells)
        if "For Mayor City of San Antonio" in row_text:
            in_mayor_section = True
            continue
        if in_mayor_section and cells and cells[0] == "Total Votes Cast":
            in_mayor_section = False
            continue
        if not in_mayor_section or len(cells) <= 2:
            continue
        candidate = normalize_candidate_name(cells[0])
        if not candidate or candidate in {"Vote For 1", "TOTAL"}:
            continue
        if not cells[2].replace(",", "").isdigit():
            continue
        votes[candidate] += int_value(cells[2])
    if not votes:
        raise RuntimeError("No San Antonio mayor rows found in Electionware CSV")
    return [{"candidate": candidate, "party": "NONPARTISAN", "votes": vote} for candidate, vote in votes.items()]


def parse_electionware_summary_pdf_text(text: str) -> list[dict[str, Any]]:
    in_mayor_section = False
    candidates = []
    for line in text.splitlines():
        normalized = clean_text(line)
        if "For Mayor City of San Antonio" in normalized:
            in_mayor_section = True
            continue
        if not in_mayor_section:
            continue
        if normalized.startswith("Total Votes Cast") or normalized.startswith("For Council"):
            break
        match = re.match(r"^([A-Za-z][A-Za-z .'\"-]+?)\s+([\d,]+)\s+\d+\.\d+%", normalized)
        if not match:
            continue
        candidates.append(
            {
                "candidate": normalize_candidate_name(match.group(1)),
                "party": "NONPARTISAN",
                "votes": int_value(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError("No San Antonio mayor rows found in Electionware PDF text")
    return candidates


def parse_electionware_media_html(page_html: str) -> list[dict[str, Any]]:
    in_mayor_section = False
    candidates = []
    for line in html.unescape(page_html).splitlines():
        normalized = clean_text(line)
        lowered = normalized.casefold()
        if lowered == "mayor" or ("mayor" in lowered and ("city of san antonio" in lowered or "cosa mayor" in lowered)):
            in_mayor_section = True
            continue
        if not in_mayor_section:
            continue
        if "city of san antonio" in lowered and "mayor" not in lowered:
            break
        if lowered.startswith(("council", "member of council", "cosa place", "city council")):
            break
        if lowered.startswith(("vote for", "(with", "over votes", "under votes")):
            continue
        match = re.match(r"^\s*(.+?)\s+(?:\.\s*)+([\d,]+)\s+(?:\d+\.\d+|\.\d+)\b", line)
        if not match:
            continue
        candidates.append(
            {
                "candidate": normalize_candidate_name(match.group(1)),
                "party": "NONPARTISAN",
                "votes": int_value(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError("No San Antonio mayor rows found in Electionware media HTML")
    return candidates


def parse_san_antonio_canvass_pdf_text(text: str) -> list[dict[str, Any]]:
    in_mayor_section = False
    candidates = []
    for line in text.splitlines():
        normalized = clean_text(line)
        if not normalized:
            continue
        if re.search(r"FOR MEMBER OF COUNCIL,\s*PLACE NO\.\s*11\s*\(MAYOR\)", normalized, flags=re.IGNORECASE):
            in_mayor_section = True
            continue
        if not in_mayor_section:
            continue
        if normalized.startswith("SECTION") or re.search(r"FOR MEMBER OF COUNCIL,\s*PLACE NO\.", normalized, flags=re.IGNORECASE):
            break
        match = re.match(r'^(?:"FOR"\s+)?(.+?)\s+-?\s*([\d,]+)(?:\s+votes?)?$', normalized, flags=re.IGNORECASE)
        if not match:
            continue
        candidates.append(
            {
                "candidate": normalize_candidate_name(match.group(1)),
                "party": "NONPARTISAN",
                "votes": int_value(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError("No San Antonio mayor rows found in canvass PDF text")
    return candidates


def is_harris_houston_mayor_heading(value: str) -> bool:
    lowered = value.casefold()
    return "city of houston" in lowered and "mayor" in lowered and "vote" in lowered


def parse_harris_cumulative_pdf_text(text: str, contest_heading: str) -> list[dict[str, Any]]:
    in_section = False
    candidates = []
    for line in text.splitlines():
        normalized = clean_text(line)
        if normalized == contest_heading or is_harris_houston_mayor_heading(normalized):
            in_section = True
            continue
        if not in_section:
            continue
        if normalized.startswith("Cast Votes:"):
            break
        if not normalized or normalized.startswith("Choice "):
            continue
        match = re.match(r"^(.+?)\s+[\d,]+\s+\d+\.\d+%.*\s+([\d,]+)\s+\d+\.\d+%$", normalized)
        if not match:
            continue
        candidates.append(
            {
                "candidate": normalize_candidate_name(match.group(1)),
                "party": "NONPARTISAN",
                "votes": int_value(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError(f"No rows found for Harris cumulative contest {contest_heading!r}")
    return candidates


def parse_houston_citysec_combined_pdf_text(text: str) -> list[dict[str, Any]]:
    in_mayor_section = False
    candidates = []
    for line in text.splitlines():
        normalized = clean_text(line)
        if normalized == "MAYOR":
            in_mayor_section = True
            continue
        if not in_mayor_section:
            continue
        if normalized.startswith("COUNCIL MEMBER"):
            break
        match = re.match(r"^(.+?)\s+([\d,]+)\s+\d+\s*\.?\s*\d+$", normalized)
        if not match:
            continue
        candidates.append(
            {
                "candidate": normalize_candidate_name(match.group(1)),
                "party": "NONPARTISAN",
                "votes": int_value(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError("No Houston mayor rows found in City Secretary combined PDF text")
    return candidates


def parse_austin_resolution_pdf_text(text: str) -> list[dict[str, Any]]:
    in_mayor_section = False
    candidates = []
    for line in text.splitlines():
        normalized = clean_text(line)
        if not normalized:
            continue
        heading = re.sub(r"^\d+\s+", "", normalized).casefold()
        if heading in {"mayor", "city mayor", "city mavor", "citv mayor", "citv mavor"}:
            in_mayor_section = True
            continue
        if not in_mayor_section:
            continue
        if re.match(r"^\d*\s*C(?:ity|itv)\s+Council\b", normalized, flags=re.IGNORECASE):
            break
        final_text = re.sub(r"\[[^\]]+\]", "", normalized)
        match = re.match(r"^(?:\d+\s+)?(.+?)\s+([\d,]+)(?:;.*)?$", final_text)
        if not match:
            continue
        candidates.append(
            {
                "candidate": normalize_candidate_name(match.group(1)),
                "party": "NONPARTISAN",
                "votes": int_value(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError("No Austin mayor rows found in resolution PDF text")
    return candidates


def parse_dallas_resolution_pdf_text(text: str) -> list[dict[str, Any]]:
    in_mayor_section = False
    candidates = []
    for line in text.splitlines():
        normalized = clean_text(line)
        if not normalized:
            continue
        if re.search(r"For Member of Council,\s*Place 15\s*(?:\(Mayor\))?:?", normalized, flags=re.IGNORECASE):
            in_mayor_section = True
            continue
        if not in_mayor_section:
            continue
        if re.search(r"For Member of Council,\s*Place\s+\d+", normalized, flags=re.IGNORECASE):
            break
        if normalized.startswith(("It appears", "WHEREAS", "NOW, THEREFORE", "SECTION")):
            break
        match = re.match(r"^(.+?)\s+([0-9Iil|r,]+)$", normalized)
        if not match:
            continue
        candidate = normalize_candidate_name(match.group(1).rstrip(":"))
        if candidate.isdigit() or candidate.casefold() in {"over votes", "under votes", "total votes cast"}:
            continue
        candidates.append(
            {
                "candidate": candidate,
                "party": "NONPARTISAN",
                "votes": int_value_with_ocr_digits(match.group(2)),
            }
        )
    if not candidates:
        raise RuntimeError("No Dallas mayor rows found in resolution PDF text")
    return candidates


def parse_dallas_master_list_pdf_text(text: str, election_file: TexasMayorElectionFile) -> list[dict[str, Any]]:
    heading_pattern = r"(?:Place\s+(?:No\.\s*)?(?:11|15)\s*(?:/|,\s*)\s*Mayor|Mayor/Place\s+(?:11|15))\s*:"
    target_date = dt.date.fromisoformat(election_file.election_date).strftime("%B %d, %Y")
    date_pattern = rf"(?:[A-Za-z]+,\s+)?{re.escape(target_date)}"
    if election_file.election_stage == "runoff":
        marker_pattern = rf"(?:Special\s+)?Run\s*Off\s+Election:\s+{date_pattern}|Special\s+Runoff\s+Election:\s+{date_pattern}"
    elif election_file.election_stage == "special":
        marker_pattern = rf"Special\s+Election:\s+{date_pattern}"
    else:
        marker_pattern = rf"(?<!Run Off )(?<!Special )Election:\s+{date_pattern}"

    matches = [
        match
        for match in re.finditer(heading_pattern, text, flags=re.IGNORECASE)
        if (re.search(marker_pattern, text[max(0, match.start() - 1800) : match.start()], flags=re.IGNORECASE) or target_date not in text)
        if "N/A" not in text[match.start() : match.start() + 120]
    ]
    candidate_sets = []
    for heading in matches:
        section = text[heading.start() : heading.start() + 1200]
        section = re.split(r"Councilmembers?:", section, maxsplit=1, flags=re.IGNORECASE)[0]
        candidates = []
        for line in section.splitlines():
            normalized = clean_text(line)
            if not normalized or normalized.startswith("Votes Cast"):
                continue
            normalized = re.sub(heading_pattern, "", normalized, count=1, flags=re.IGNORECASE)
            if not normalized:
                continue
            row = re.match(r"^(.+?)\s+([\d,]+)$", normalized)
            if not row:
                continue
            candidates.append(
                {
                    "candidate": normalize_candidate_name(row.group(1)),
                    "party": "NONPARTISAN",
                    "votes": int_value(row.group(2)),
                }
            )
        if candidates:
            candidate_sets.append(candidates)
    if candidate_sets:
        return candidate_sets[-1] if election_file.election_stage == "runoff" else candidate_sets[0]
    if not matches:
        raise RuntimeError("No Dallas master list mayor heading found")
    raise RuntimeError("No Dallas master list mayor rows found")


def build_file_contest(source: TexasMayorSource, election_file: TexasMayorElectionFile, contest_id: int) -> dict[str, Any]:
    if election_file.format == "electionware-precinct-csv":
        data = cached_fetch_bytes(election_file.url)
        candidates = parse_electionware_mayor_csv(data.decode("utf-8-sig", errors="replace"))
    elif election_file.format == "electionware-summary-pdf":
        candidates = parse_electionware_summary_pdf_text(cached_pdf_to_text(election_file))
    elif election_file.format == "electionware-media-html":
        data = cached_fetch_bytes(election_file.url)
        candidates = parse_electionware_media_html(decode_source_text(data))
    elif election_file.format == "san-antonio-canvass-pdf":
        candidates = parse_san_antonio_canvass_pdf_text(cached_pdf_to_text(election_file))
    elif election_file.format == "harris-cumulative-pdf":
        candidates = parse_harris_cumulative_pdf_text(cached_pdf_to_text(election_file), "City of Houston, Mayor - Vote for none or one")
    elif election_file.format == "houston-citysec-combined-pdf":
        candidates = parse_houston_citysec_combined_pdf_text(cached_pdf_to_text(election_file))
    elif election_file.format == "austin-resolution-pdf":
        candidates = parse_austin_resolution_pdf_text(cached_pdf_to_text(election_file))
    elif election_file.format == "dallas-resolution-pdf":
        candidates = parse_dallas_resolution_pdf_text(cached_pdf_to_text(election_file))
    elif election_file.format == "dallas-resolution-ocr-pdf":
        candidates = parse_dallas_resolution_pdf_text(cached_pdf_to_ocr_text(election_file))
    elif election_file.format == "dallas-master-list-pdf":
        candidates = parse_dallas_master_list_pdf_text(cached_pdf_to_text(election_file), election_file)
    else:
        raise RuntimeError(f"Unsupported Texas mayor source format: {election_file.format}")
    return materialize_mayor_contest(source, election_file, candidates, contest_id)


def build_source_summary(source: TexasMayorSource, contest_start_id: int) -> tuple[dict[str, Any], int]:
    contests = []
    contest_id = contest_start_id
    if source.url:
        for block in parse_tables(fetch_html(source.url)):
            contest = build_contest(source, block, contest_id)
            if contest is not None:
                contests.append(contest)
                contest_id += 1
    for election_file in source.election_files:
        contests.append(build_file_contest(source, election_file, contest_id))
        contest_id += 1
    contests.sort(key=lambda contest: (contest["election_date"], contest["election_stage"]))
    for index, contest in enumerate(contests, start=contest_start_id):
        contest["contest_id"] = index
    years = sorted({contest["year"] for contest in contests})
    return (
        {
            "place": source.place,
            "state": "Texas",
            "state_po": "TX",
            "years": years,
            "source": {
                "name": source.source_name,
                "url": source.url or source.homepage,
                "homepage": source.homepage,
                "official": True,
                "quality_grade": "A",
            },
            "contests": contests,
        },
        contest_start_id + len(contests),
    )


def build_summary() -> dict[str, Any]:
    places = []
    contest_id = 1
    for source in MAYOR_SOURCES:
        place_summary, contest_id = build_source_summary(source, contest_id)
        places.append(place_summary)
    return {
        "source": {
            "name": "Texas municipal election archives",
            "url": "https://www.fortworthtexas.gov/departments/citysecretary/elections/election-history",
            "official": True,
            "quality_grade": "A",
        },
        "state_po": "TX",
        "scope": "municipal_mayors",
        "places": places,
    }


def main() -> None:
    summary = build_summary()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    contest_count = sum(len(place["contests"]) for place in summary["places"])
    print(f"Wrote {OUTPUT_PATH} with {contest_count} Texas mayor contests.")


if __name__ == "__main__":
    main()
