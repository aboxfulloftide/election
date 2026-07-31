#!/usr/bin/env python3
"""Replace partial 2022 Kentucky U.S. House contests with validated certified rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from parse_kentucky_certified import build_us_house_contests


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT_DIR / "data/raw/official/kentucky/2022_certified_general_election_results_ocr.txt"
SUMMARY_PATH = ROOT_DIR / "public/results/kentucky-statewide-summary.json"


def merge(input_path: Path = INPUT_PATH, summary_path: Path = SUMMARY_PATH) -> int:
    contests = build_us_house_contests(input_path.read_text(encoding="utf-8"))
    if len(contests) != 6 or not all(contest["validated"] for contest in contests):
        raise RuntimeError("Kentucky certified U.S. House contests did not fully reconcile")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    house_by_district = {contest["district_number"]: contest for contest in contests}
    for election in summary["elections"]:
        if election["election"]["year"] != 2022:
            continue
        replaced = []
        for contest in election["contests"]:
            if contest.get("office") == "U.S. House" and contest.get("district_number") in house_by_district:
                certified = house_by_district[contest["district_number"]]
                certified["contest_id"] = contest["contest_id"]
                certified.pop("candidate_votes_total", None)
                certified.pop("validated", None)
                certified.pop("corrections_applied", None)
                certified["official"] = True
                replaced.append(certified)
            else:
                replaced.append(contest)
        election["contests"] = replaced
    summary["source"]["certified_federal_overrides"] = ["2022 U.S. House"]
    summary_path.write_text(json.dumps(summary, separators=(",", ":")), encoding="utf-8")
    print(f"Replaced {len(contests)} Kentucky 2022 U.S. House contests in {summary_path.relative_to(ROOT_DIR)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT_DIR / args.input
    summary_path = args.summary if args.summary.is_absolute() else ROOT_DIR / args.summary
    return merge(input_path, summary_path)


if __name__ == "__main__":
    raise SystemExit(main())
