#!/usr/bin/env python3
"""Download MIT county presidential returns and build app-ready JSON."""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any


BASE_URL = "https://dataverse.harvard.edu"
DOI = "doi:10.7910/DVN/VOQCHQ"
DATASET_API = f"{BASE_URL}/api/datasets/:persistentId/?persistentId={DOI}"
FILES_API = f"{BASE_URL}/api/datasets/:persistentId/versions/:latest/files?persistentId={DOI}"
GUESTBOOK_ID = 458
RESULTS_LABEL = "countypres_2000-2024.tab"
CODEBOOK_LABEL = "County Presidential Returns 2000-2024.md"
RAW_DIR = Path("data/raw")
PUBLIC_RESULTS_DIR = Path("public/results")
SUMMARY_PATH = PUBLIC_RESULTS_DIR / "county-presidential-summary.json"


def request_json(url: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "election-night-map/0.1 (+https://github.com/)",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {detail}") from exc


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        with path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)


def guestbook_response() -> dict[str, Any]:
    return {
        "guestbookResponse": {
            "name": os.environ.get("ELECTION_DATA_NAME", "Election Night Map Developer"),
            "email": os.environ.get("ELECTION_DATA_EMAIL", "dev@example.com"),
            "institution": os.environ.get("ELECTION_DATA_INSTITUTION", "Independent"),
            "position": os.environ.get("ELECTION_DATA_POSITION", "Developer"),
        }
    }


def signed_download_url(file_id: int) -> str:
    response = request_json(
        f"{BASE_URL}/api/access/datafile/{file_id}",
        method="POST",
        body=guestbook_response(),
    )
    return response["data"]["signedUrl"]


def find_file_id(files: list[dict[str, Any]], label: str) -> int:
    for item in files:
        if item.get("label") == label:
            return int(item["dataFile"]["id"])
    raise RuntimeError(f"Could not find Dataverse file labeled {label!r}")


def parse_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def normalize_fips(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    return value.zfill(5)


def build_summary(raw_results_path: Path, dataset_meta: dict[str, Any]) -> dict[str, Any]:
    county_rows: dict[str, dict[str, Any]] = {}
    years: set[int] = set()

    with raw_results_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row.get("mode") != "TOTAL":
                continue

            fips = normalize_fips(row.get("county_fips", ""))
            if not fips:
                continue

            year = int(row["year"])
            years.add(year)

            county = county_rows.setdefault(
                fips,
                {
                    "fips": fips,
                    "state": row["state"],
                    "state_po": row["state_po"],
                    "county_name": row["county_name"],
                    "results": {},
                },
            )
            result = county["results"].setdefault(
                str(year),
                {
                    "totalvotes": parse_int(row.get("totalvotes")),
                    "parties": {},
                },
            )
            party = (row.get("party") or "OTHER").upper()
            result["parties"][party] = result["parties"].get(party, 0) + parse_int(row.get("candidatevotes"))

    for county in county_rows.values():
        for result in county["results"].values():
            parties = result["parties"]
            total = result["totalvotes"] or sum(parties.values())
            ordered = sorted(parties.items(), key=lambda item: item[1], reverse=True)
            winner_party, winner_votes = ordered[0] if ordered else ("OTHER", 0)
            runner_up_votes = ordered[1][1] if len(ordered) > 1 else 0
            dem_votes = parties.get("DEMOCRAT", 0)
            rep_votes = parties.get("REPUBLICAN", 0)
            margin_votes = winner_votes - runner_up_votes

            result["totalvotes"] = total
            result["winner_party"] = winner_party
            result["winner_votes"] = winner_votes
            result["margin_votes"] = margin_votes
            result["margin_pct"] = round((margin_votes / total) * 100, 2) if total else 0
            result["dem_share"] = round((dem_votes / total) * 100, 2) if total else 0
            result["rep_share"] = round((rep_votes / total) * 100, 2) if total else 0
            result["two_party_margin"] = round(((dem_votes - rep_votes) / total) * 100, 2) if total else 0

    version = dataset_meta["data"]["latestVersion"]
    return {
        "source": {
            "name": "MIT Election Data and Science Lab, County Presidential Election Returns 2000-2024",
            "doi": DOI,
            "url": "https://doi.org/10.7910/DVN/VOQCHQ",
            "retrieved_at": dt.datetime.now(dt.UTC).isoformat(),
            "dataverse_version": f'{version["versionNumber"]}.{version["versionMinorNumber"]}',
            "dataverse_release_time": version.get("releaseTime"),
            "license": version.get("license", {}).get("name"),
        },
        "years": sorted(years),
        "counties": sorted(county_rows.values(), key=lambda item: item["fips"]),
    }


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    dataset_meta = request_json(DATASET_API)
    files = request_json(FILES_API)["data"]
    results_id = find_file_id(files, RESULTS_LABEL)
    codebook_id = find_file_id(files, CODEBOOK_LABEL)

    results_path = RAW_DIR / RESULTS_LABEL
    codebook_path = RAW_DIR / CODEBOOK_LABEL

    print(f"Downloading {RESULTS_LABEL}...")
    download(signed_download_url(results_id), results_path)

    print(f"Downloading {CODEBOOK_LABEL}...")
    download(signed_download_url(codebook_id), codebook_path)

    print("Building county summary...")
    summary = build_summary(results_path, dataset_meta)
    SUMMARY_PATH.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")

    print(f"Wrote {SUMMARY_PATH} with {len(summary['counties'])} counties and {len(summary['years'])} years.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
