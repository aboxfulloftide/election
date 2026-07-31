"""Configuration for Florida municipal mayor summary pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "public/results/florida-mayor-summary.json"


@dataclass(frozen=True)
class FloridaMayorSource:
    year: int
    election_date: str
    election_name: str
    county: str
    county_fips: str
    source_name: str
    homepage: str
    url: str
    default_place: str | None = None


MIAMI_DADE_HOMEPAGE = "https://www.votemiamidade.gov/elections/data/results-archive.page"
HILLSBOROUGH_HOMEPAGE = "https://www.votehillsborough.gov/183/Election-Results"
DUVAL_HOMEPAGE = "https://www.duvalelections.gov/Archive.aspx?AMID=36"
ORANGE_HOMEPAGE = "https://voteorangefl.gov/election-record/2023-special-house-35-primary-and-city-orlando-general-2023-11-07/"


MAYOR_SOURCES = [
    FloridaMayorSource(
        year=2021,
        election_date="2021-11-02",
        election_name="Hialeah, Miami, Miami Beach, Special (Biscayne Gardens) and Sunny Isles Beach Elections",
        county="Miami-Dade",
        county_fips="12086",
        source_name="Miami-Dade County Supervisor of Elections Election Night Reporting",
        homepage=MIAMI_DADE_HOMEPAGE,
        url="https://enr.electionsfl.org/DAD/3110/Summary/",
    ),
    FloridaMayorSource(
        year=2021,
        election_date="2021-11-16",
        election_name="Hialeah, Miami Beach and Sunny Isles Beach Run-Off Elections",
        county="Miami-Dade",
        county_fips="12086",
        source_name="Miami-Dade County Supervisor of Elections Election Night Reporting",
        homepage=MIAMI_DADE_HOMEPAGE,
        url="https://enr.electionsfl.org/DAD/3116/Summary/",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-11-07",
        election_name="Hialeah, Miami, Miami Beach and Surfside Elections",
        county="Miami-Dade",
        county_fips="12086",
        source_name="Miami-Dade County Supervisor of Elections Election Night Reporting",
        homepage=MIAMI_DADE_HOMEPAGE,
        url="https://enr.electionsfl.org/DAD/3450/Summary/",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-11-21",
        election_name="Miami and Miami Beach Run-Off Elections",
        county="Miami-Dade",
        county_fips="12086",
        source_name="Miami-Dade County Supervisor of Elections Election Night Reporting",
        homepage=MIAMI_DADE_HOMEPAGE,
        url="https://enr.electionsfl.org/DAD/3478/Summary/",
    ),
    FloridaMayorSource(
        year=2015,
        election_date="2015-03-03",
        election_name="City of Tampa Municipal Election",
        county="Hillsborough",
        county_fips="12057",
        source_name="Hillsborough County Supervisor of Elections Election Night Reporting",
        homepage=HILLSBOROUGH_HOMEPAGE,
        url="https://enr.electionsfl.org/HIL/Summary/1246/",
        default_place="Tampa",
    ),
    FloridaMayorSource(
        year=2015,
        election_date="2015-03-24",
        election_name="City of Tampa Municipal Runoff Election",
        county="Hillsborough",
        county_fips="12057",
        source_name="Hillsborough County Supervisor of Elections Election Night Reporting",
        homepage=HILLSBOROUGH_HOMEPAGE,
        url="https://enr.electionsfl.org/HIL/Summary/1258/",
        default_place="Tampa",
    ),
    FloridaMayorSource(
        year=2019,
        election_date="2019-03-05",
        election_name="City of Tampa Municipal Election",
        county="Hillsborough",
        county_fips="12057",
        source_name="Hillsborough County Supervisor of Elections Election Night Reporting",
        homepage=HILLSBOROUGH_HOMEPAGE,
        url="https://enr.electionsfl.org/HIL/2083/Summary/",
        default_place="Tampa",
    ),
    FloridaMayorSource(
        year=2019,
        election_date="2019-04-23",
        election_name="City of Tampa Municipal Runoff Election",
        county="Hillsborough",
        county_fips="12057",
        source_name="Hillsborough County Supervisor of Elections Election Night Reporting",
        homepage=HILLSBOROUGH_HOMEPAGE,
        url="https://enr.electionsfl.org/HIL/Summary/2119/",
        default_place="Tampa",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-03-07",
        election_name="City of Tampa Municipal Election",
        county="Hillsborough",
        county_fips="12057",
        source_name="Hillsborough County Supervisor of Elections Election Night Reporting",
        homepage=HILLSBOROUGH_HOMEPAGE,
        url="https://enr.electionsfl.org/HIL/Summary/3362/",
        default_place="Tampa",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-04-25",
        election_name="City of Tampa Municipal Runoff Election",
        county="Hillsborough",
        county_fips="12057",
        source_name="Hillsborough County Supervisor of Elections Election Night Reporting",
        homepage=HILLSBOROUGH_HOMEPAGE,
        url="https://enr.electionsfl.org/HIL/3388/Summary/",
        default_place="Tampa",
    ),
    FloridaMayorSource(
        year=2015,
        election_date="2015-03-24",
        election_name="Duval First Election",
        county="Duval",
        county_fips="12031",
        source_name="Duval County Supervisor of Elections Election Night Reporting",
        homepage=DUVAL_HOMEPAGE,
        url="https://enr.electionsfl.org/DUV/Summary/1251/",
        default_place="Jacksonville",
    ),
    FloridaMayorSource(
        year=2015,
        election_date="2015-05-19",
        election_name="Duval General Election",
        county="Duval",
        county_fips="12031",
        source_name="Duval County Supervisor of Elections Election Night Reporting",
        homepage=DUVAL_HOMEPAGE,
        url="https://enr.electionsfl.org/DUV/Summary/1276/",
        default_place="Jacksonville",
    ),
    FloridaMayorSource(
        year=2019,
        election_date="2019-03-19",
        election_name="Duval First Election",
        county="Duval",
        county_fips="12031",
        source_name="Duval County Supervisor of Elections Election Night Reporting",
        homepage=DUVAL_HOMEPAGE,
        url="https://enr.electionsfl.org/DUV/Summary/2085/",
        default_place="Jacksonville",
    ),
    FloridaMayorSource(
        year=2019,
        election_date="2019-05-14",
        election_name="Duval General Election",
        county="Duval",
        county_fips="12031",
        source_name="Duval County Supervisor of Elections Election Night Reporting",
        homepage=DUVAL_HOMEPAGE,
        url="https://enr.electionsfl.org/DUV/Summary/2125/",
        default_place="Jacksonville",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-03-21",
        election_name="Duval First Election",
        county="Duval",
        county_fips="12031",
        source_name="Duval County Supervisor of Elections Election Night Reporting",
        homepage=DUVAL_HOMEPAGE,
        url="https://enr.electionsfl.org/DUV/Summary/3353/",
        default_place="Jacksonville",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-05-16",
        election_name="Duval General Election",
        county="Duval",
        county_fips="12031",
        source_name="Duval County Supervisor of Elections Election Night Reporting",
        homepage=DUVAL_HOMEPAGE,
        url="https://enr.electionsfl.org/DUV/Summary/3385/",
        default_place="Jacksonville",
    ),
    FloridaMayorSource(
        year=2023,
        election_date="2023-11-07",
        election_name="2023 Special House District 35 Primary and City of Orlando General",
        county="Orange",
        county_fips="12095",
        source_name="Orange County Supervisor of Elections Election Night Reporting",
        homepage=ORANGE_HOMEPAGE,
        url="https://enr.electionsfl.org/ORA/3462/Summary/",
        default_place="Orlando",
    ),
]
