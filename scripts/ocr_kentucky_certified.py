#!/usr/bin/env python3
"""Create a searchable text layer for Kentucky's image-only certified PDF."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/kentucky"
SOURCE_PATH = RAW_DIR / "2022_certified_general_election_results.pdf"
OCR_PDF_PATH = RAW_DIR / "2022_certified_general_election_results_ocr.pdf"
TEXT_PATH = RAW_DIR / "2022_certified_general_election_results_ocr.txt"


def run(source: Path = SOURCE_PATH, ocr_pdf: Path = OCR_PDF_PATH, text: Path = TEXT_PATH, workers: int = 4, force: bool = False) -> None:
    """Run OCRmyPDF and extract layout-preserving text."""
    for path in (ocr_pdf, text):
        path.parent.mkdir(parents=True, exist_ok=True)
    if force or not ocr_pdf.exists():
        subprocess.run(
            [
                "ocrmypdf",
                "--deskew",
                "--force-ocr",
                "--output-type",
                "pdf",
                "--optimize",
                "0",
                "--jobs",
                str(workers),
                str(source),
                str(ocr_pdf),
            ],
            check=True,
        )
    subprocess.run(["pdftotext", "-layout", str(ocr_pdf), str(text)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--source", type=Path, default=SOURCE_PATH)
    parser.add_argument("--output", type=Path, default=OCR_PDF_PATH)
    parser.add_argument("--text", type=Path, default=TEXT_PATH)
    args = parser.parse_args()
    paths = [path if path.is_absolute() else ROOT_DIR / path for path in (args.source, args.output, args.text)]
    run(paths[0], paths[1], paths[2], args.workers, args.force)
    print(f"Wrote {paths[2].relative_to(ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
