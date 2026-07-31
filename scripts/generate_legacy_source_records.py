#!/usr/bin/env python3
"""Create explicit official source records for the first legacy cohort.

These records identify official archives without claiming that a file has
already been downloaded or parsed.  Importers can replace each record's
status after source acquisition and reconciliation.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT_DIR / "data/source-registry"
DOC_PATH = ROOT_DIR / "docs/sources/legacy-cohort-01.md"
STATES = [
    ("AL", "Alabama", "https://www.sos.alabama.gov/alabama-votes/election-information/election-data", "official PDF/HTML archive"),
    ("AK", "Alaska", "https://www.elections.alaska.gov/doc/info/ElectionResults.php", "official PDF/HTML archive"),
    ("AZ", "Arizona", "https://apps.azsos.gov/election/2010/General/ElectionInformation.htm", "cycle pages with official canvass PDF and precinct files"),
    ("AR", "Arkansas", "https://www.sos.arkansas.gov/elections/research/election-results", "official election-results archive"),
    ("CO", "Colorado", "https://www.sos.state.co.us/pubs/elections/Results/archive2000.html", "official PDF and precinct-level XLSX archive"),
    ("CT", "Connecticut", "https://portal.ct.gov/sots/election-services/statement-of-vote-pdfs/general-elections-statement-of-vote-1922", "official Statement of Vote PDF archive"),
    ("DE", "Delaware", "https://elections.delaware.gov/elections/election_archive.html", "official raw-data and results archive"),
    ("HI", "Hawaii", "https://elections.hawaii.gov/election-result/2010-general-election/", "official certified PDF and text reports"),
    ("ID", "Idaho", "https://sos.idaho.gov/elections-division/idaho-election-results/", "official statewide, county, and Excel archive"),
    ("IL", "Illinois", "https://www.elections.il.gov/PDFSiteMapProd.htm", "official downloadable vote-total and office CSV archive"),
]
OFFICES = ["President", "U.S. Senate", "U.S. House", "Governor", "State Senate", "State House"]
YEARS = [2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018]


def build_registry(state_po: str, state: str, url: str, format_note: str) -> dict:
    entries = []
    for year in YEARS:
        wave = "2000-2008" if year <= 2008 else "2010-2018"
        entries.append(
            {
                "id": f"{state_po.lower()}-official-{year}-legacy-source",
                "scope": "statewide",
                "offices": OFFICES,
                "years": [year],
                "status": "source_identified",
                "format": format_note,
                "geography": "statewide-county-or-district",
                "quality_grade": None,
                "parser": f"planned:legacy-{state_po.lower()}-{year}-import",
                "urls": [url],
                "notes": f"{state} official {year} general-election archive identified for the {wave} wave. File acquisition, format audit, district-cycle review, and reconciliation are still required before import.",
            }
        )
    return {"state": state, "state_po": state_po, "entries": entries}


def build_doc() -> str:
    lines = [
        "# Legacy Cohort 01 Sources",
        "",
        "This source-discovery record covers the first ten-state cohort for both legacy waves. Every year is explicitly registered as `source_identified`; none is marked imported until an official file is staged, parsed, reconciled, and tested.",
        "",
        "| State | Official archive | Format lead | Years |",
        "| --- | --- | --- | --- |",
    ]
    for state_po, state, url, format_note in STATES:
        lines.append(f"| {state} ({state_po}) | [{url}]({url}) | {format_note} | 2000-2018 even-year generals |")
    lines.extend(
        [
            "",
            "## Processing Order",
            "",
            "1. Stage official structured files first, especially Colorado, Delaware, Idaho, and Illinois downloadable tables.",
            "2. Stage official PDF/HTML canvasses for Alabama, Alaska, Arizona, Arkansas, Connecticut, and Hawaii.",
            "3. Record the election-cycle district schema before normalizing State Senate, State House, and U.S. House contests.",
            "4. Use compiled data only after the official archive has been searched and the gap is documented in the source registry.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    for state_po, state, url, format_note in STATES:
        path = REGISTRY_DIR / f"{state.lower().replace(' ', '-')}.json"
        path.write_text(json.dumps(build_registry(state_po, state, url, format_note), indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT_DIR)}")
    DOC_PATH.write_text(build_doc(), encoding="utf-8")
    print(f"Wrote {DOC_PATH.relative_to(ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
