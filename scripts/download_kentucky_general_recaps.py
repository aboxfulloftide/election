#!/usr/bin/env python3
"""Download Kentucky official county recap PDFs for a general election."""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/kentucky"
BASE_URL = "https://elect.ky.gov"
PAGES = {
    2022: "/results/2020-2029/Pages/2022-General-Recap-Sheets.aspx",
    2024: "/results/2020-2029/Pages/2024General-Recap-Sheets.aspx",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        if "GeneralRecaps" in href and re.search(r"\.(pdf|xlsx)$", href, re.I):
            self.links.append(href)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "election-night-map/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def discover(year: int) -> list[str]:
    page_url = BASE_URL + PAGES[year]
    parser = LinkParser()
    parser.feed(fetch(page_url).decode("utf-8", errors="replace"))
    links = sorted(set(urllib.parse.urljoin(page_url, link) for link in parser.links))
    if len(links) < 100:
        raise RuntimeError(f"Expected at least 100 Kentucky county recap links for {year}, found {len(links)}")
    return links


def destination(year: int, url: str) -> Path:
    name = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return RAW_DIR / f"{year}_{safe_name}"


def download_one(item: tuple[int, str]) -> tuple[str, str]:
    year, url = item
    path = destination(year, url)
    if path.exists() and path.stat().st_size > 1000:
        return "existing", path.name
    data = fetch(url)
    if not data.startswith(b"%PDF") and not data.startswith(b"PK"):
        raise RuntimeError(f"Unexpected response for {url}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return "downloaded", path.name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, choices=sorted(PAGES), action="append")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    years = args.year or sorted(PAGES)
    links = [(year, url) for year in years for url in discover(year)]
    counts = {"downloaded": 0, "existing": 0}
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        for future in concurrent.futures.as_completed([executor.submit(download_one, item) for item in links]):
            try:
                status, name = future.result()
                counts[status] += 1
                print(f"{status}: {name}")
            except Exception as exc:
                failures.append(str(exc))
    if failures:
        for failure in failures:
            print(f"failed: {failure}")
        raise SystemExit(f"{len(failures)} Kentucky recap downloads failed")
    print(f"Kentucky recap download complete: {counts['downloaded']} downloaded, {counts['existing']} already staged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
