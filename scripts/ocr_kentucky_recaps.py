#!/usr/bin/env python3
"""Stage OCR text for Kentucky recap PDFs whose text layer is blank."""

from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/kentucky"
OCR_DIR = RAW_DIR / "ocr"


def native_text(path: Path) -> str:
    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    ).stdout


def output_path(path: Path) -> Path:
    return OCR_DIR / f"{path.stem}.txt"


def ocr_pdf(path: Path, dpi: int = 100, psm: int = 4) -> Path:
    destination = output_path(path)
    if destination.exists() and destination.stat().st_size > 100:
        return destination
    with tempfile.TemporaryDirectory(prefix="ky-ocr-") as temporary:
        prefix = Path(temporary) / "page"
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(path), str(prefix)], check=True, capture_output=True)
        pages = sorted(Path(temporary).glob("page-*.png"))
        if not pages:
            raise RuntimeError(f"No rendered pages for {path.name}")
        chunks = []
        for page in pages:
            result = subprocess.run(
                ["tesseract", str(page), "stdout", "--psm", str(psm)],
                check=True,
                capture_output=True,
                text=True,
                errors="replace",
            )
            chunks.append(result.stdout)
    text = "\n\f\n".join(chunks).strip() + "\n"
    if len(text) < 100:
        raise RuntimeError(f"OCR produced too little text for {path.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return destination


def candidates(year: int | None, requested: list[str]) -> list[Path]:
    if requested:
        paths = [RAW_DIR / name for name in requested]
    else:
        paths = sorted(RAW_DIR.glob(f"{year or 20}*_*.pdf"))
    return [path for path in paths if path.exists() and not native_text(path).strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, choices=(2022, 2024))
    parser.add_argument("--file", action="append", default=[], help="Specific staged PDF filename; repeatable.")
    parser.add_argument("--limit", type=int, help="Process at most this many blank PDFs.")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--psm", type=int, default=4, help="Tesseract page segmentation mode.")
    args = parser.parse_args()
    selected = candidates(args.year, args.file)
    if args.limit:
        selected = selected[: args.limit]
    if not selected:
        print("No blank Kentucky recap PDFs selected.")
        return 0
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(ocr_pdf, path, 100, args.psm): path for path in selected}
        for future in concurrent.futures.as_completed(futures):
            path = futures[future]
            try:
                print(f"staged OCR: {future.result().relative_to(ROOT_DIR)}")
            except Exception as exc:
                failures.append(f"{path.name}: {exc}")
    for failure in failures:
        print(f"failed: {failure}")
    if failures:
        raise SystemExit(f"{len(failures)} Kentucky OCR jobs failed")
    print(f"Kentucky OCR staging complete: {len(selected)} PDFs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
