#!/usr/bin/env python3
"""Download raw MIT county presidential returns from Harvard Dataverse."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
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


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    request_json(DATASET_API)
    files = request_json(FILES_API)["data"]
    results_id = find_file_id(files, RESULTS_LABEL)
    codebook_id = find_file_id(files, CODEBOOK_LABEL)

    results_path = RAW_DIR / RESULTS_LABEL
    codebook_path = RAW_DIR / CODEBOOK_LABEL

    print(f"Downloading {RESULTS_LABEL}...")
    download(signed_download_url(results_id), results_path)

    print(f"Downloading {CODEBOOK_LABEL}...")
    download(signed_download_url(codebook_id), codebook_path)

    print(f"Downloaded raw files to {RAW_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
