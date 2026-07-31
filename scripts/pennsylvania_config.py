"""Official Pennsylvania election returns source configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data/raw/official/pennsylvania"
OUTPUT_PATH = ROOT_DIR / "public/results/pennsylvania-statewide-summary.json"
SOURCE_PAGE_URL = "https://www.pa.gov/agencies/dos/resources/voting-and-elections-resources/voting-and-election-statistics/election-data"


@dataclass(frozen=True)
class PennsylvaniaGeneralSource:
    year: int
    election_date: str
    readme_url: str
    results_url: str
    readme_file_name: str
    results_file_name: str


PENNSYLVANIA_GENERAL_SOURCES = [
    PennsylvaniaGeneralSource(
        year=2024,
        election_date="2024-11-05",
        readme_url="https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/bulk-data/2024-general-election/er/erstat_2024_g_readme.txt",
        results_url="https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/bulk-data/2024-general-election/er/erstat_2024_g_268768_20250129.txt",
        readme_file_name="erstat-2024-general-readme.txt",
        results_file_name="erstat-2024-general-precinct-returns.txt",
    ),
    PennsylvaniaGeneralSource(
        year=2022,
        election_date="2022-11-08",
        readme_url="https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/bulk-data/ElectionReturns_2022_General_Readme.txt",
        results_url="https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/bulk-data/ElectionReturns_2022_General_PrecinctReturns.txt",
        readme_file_name="electionreturns-2022-general-readme.txt",
        results_file_name="electionreturns-2022-general-precinct-returns.txt",
    ),
    PennsylvaniaGeneralSource(
        year=2020,
        election_date="2020-11-03",
        readme_url="https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/bulk-data/ElectionReturns_2020_General_ReadMeFile.txt",
        results_url="https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/bulk-data/ElectionReturns_2020_General_PrecinctReturns.txt",
        readme_file_name="electionreturns-2020-general-readme.txt",
        results_file_name="electionreturns-2020-general-precinct-returns.txt",
    ),
]


def readme_path(source: PennsylvaniaGeneralSource) -> Path:
    return RAW_DIR / source.readme_file_name


def results_path(source: PennsylvaniaGeneralSource) -> Path:
    return RAW_DIR / source.results_file_name
