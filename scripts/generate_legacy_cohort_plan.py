#!/usr/bin/env python3
"""Generate five parallel ten-state cohort plans for each legacy wave."""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
OFFICES = ["President", "U.S. Senate", "U.S. House", "Governor", "State Senate", "State House"]


def build(wave: str, years: list[int]) -> dict:
    cohorts = []
    for index in range(5):
        states = STATES[index * 10 : (index + 1) * 10]
        cohorts.append({"id": f"{wave}-cohort-{index + 1:02d}", "states": states, "years": years, "status": "active" if index == 0 else "queued", "next_action": "Acquire official sources, build repeatable parsers, reconcile contests, and update registry/output/tests."})
    return {"wave": wave, "scope": "federal-and-state", "years": years, "offices": OFFICES, "cohorts": cohorts, "completion_rule": "Every applicable cell in a cohort must have source metadata, normalized contests, reconciliation tests, generated output, and documentation."}


def main() -> int:
    outputs = [("2010-2018", [2010, 2012, 2014, 2016, 2018]), ("2000-2008", [2000, 2002, 2004, 2006, 2008])]
    for wave, years in outputs:
        path = ROOT_DIR / f"data/national-cohorts/{wave}-cohorts.json"
        path.write_text(json.dumps(build(wave, years), indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
