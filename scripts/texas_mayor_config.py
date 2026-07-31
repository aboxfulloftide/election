"""Configuration for Texas municipal mayor summary pages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "public/results/texas-mayor-summary.json"


@dataclass(frozen=True)
class TexasMayorElectionFile:
    year: int
    election_date: str
    election_stage: str
    election_name: str
    url: str
    format: str
    quality_grade: str = "A"
    county_portion_fips: dict[str, str] | None = None


@dataclass(frozen=True)
class TexasMayorSource:
    place: str
    source_name: str
    homepage: str
    url: str | None
    county_portion_fips: dict[str, str]
    election_files: tuple[TexasMayorElectionFile, ...] = ()


FORT_WORTH_SOURCE = TexasMayorSource(
    place="Fort Worth",
    source_name="City of Fort Worth City Secretary Election History",
    homepage="https://www.fortworthtexas.gov/departments/citysecretary/elections/election-history",
    url="https://www.fortworthtexas.gov/departments/citysecretary/elections/election-history",
    county_portion_fips={
        "Tarrant County": "48439",
        "Denton County": "48121",
        "Parker County": "48367",
    },
)


SAN_ANTONIO_SOURCE = TexasMayorSource(
    place="San Antonio",
    source_name="Bexar County Elections Department Historical Election Results",
    homepage="https://www.bexar.org/2186/Historical-Election-Results",
    url=None,
    county_portion_fips={"Bexar County": "48029"},
    election_files=(
        TexasMayorElectionFile(
            year=1999,
            election_date="1999-05-01",
            election_stage="general",
            election_name="May 1, 1999 City of San Antonio General Election",
            url="https://webapp9.sanantonio.gov/FileNetArchive/%7B6EE90B1B-1AAA-4BC4-BEA0-21A73768ED13%7D/%7B6EE90B1B-1AAA-4BC4-BEA0-21A73768ED13%7D.pdf",
            format="san-antonio-canvass-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2003,
            election_date="2003-05-03",
            election_stage="general",
            election_name="May 3, 2003 City of San Antonio General Election",
            url="https://webapp9.sanantonio.gov/FileNetArchive/%7BA3B0893F-F0CD-4CBE-A5ED-1C8909C4881E%7D/%7BA3B0893F-F0CD-4CBE-A5ED-1C8909C4881E%7D.pdf",
            format="san-antonio-canvass-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2005,
            election_date="2005-05-07",
            election_stage="general",
            election_name="May 7, 2005 Joint General and Special Election",
            url="https://webapp9.sanantonio.gov/FileNetArchive/%7B0A936726-A7B0-4649-A0B3-369A7D0925E3%7D/%7B0A936726-A7B0-4649-A0B3-369A7D0925E3%7D.pdf",
            format="san-antonio-canvass-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2005,
            election_date="2005-06-07",
            election_stage="runoff",
            election_name="June 7, 2005 City of San Antonio Runoff Election",
            url="https://webapp9.sanantonio.gov/FileNetArchive/%7B37D24024-9732-4700-A3F4-94F73CC118FD%7D/%7B37D24024-9732-4700-A3F4-94F73CC118FD%7D.pdf",
            format="san-antonio-canvass-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2007,
            election_date="2007-05-12",
            election_stage="general",
            election_name="May 12, 2007 Amendment, Joint, General, Special, and Bond Election",
            url="https://webapp9.sanantonio.gov/FileNetArchive/%7B248A1F79-FCBE-4EA7-83EB-C9CD7F96C378%7D/%7B248A1F79-FCBE-4EA7-83EB-C9CD7F96C378%7D.pdf",
            format="san-antonio-canvass-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2009,
            election_date="2009-05-09",
            election_stage="general",
            election_name="May 9, 2009 Joint General Election",
            url="https://www.bexar.org/DocumentCenter/View/8946/May-9-2009-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2011,
            election_date="2011-05-14",
            election_stage="general",
            election_name="May 14, 2011 Joint General Election",
            url="https://www.bexar.org/DocumentCenter/View/7502/May-14-2011-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2013,
            election_date="2013-05-11",
            election_stage="general",
            election_name="May 11, 2013 Joint General Election",
            url="https://www.bexar.org/DocumentCenter/View/7471/May-11-2013-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2015,
            election_date="2015-05-09",
            election_stage="general",
            election_name="May 9, 2015 Joint General Election",
            url="https://www.bexar.org/DocumentCenter/View/7424/May-9-2015-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2015,
            election_date="2015-06-13",
            election_stage="runoff",
            election_name="June 13, 2015 Joint Runoff Election",
            url="https://www.bexar.org/DocumentCenter/View/7428/June-13-2015-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2017,
            election_date="2017-05-06",
            election_stage="general",
            election_name="May 6, 2017 Joint General Election",
            url="https://www.bexar.org/DocumentCenter/View/11655/May-6-2017-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2017,
            election_date="2017-06-10",
            election_stage="runoff",
            election_name="June 10, 2017 Joint Runoff Election",
            url="https://www.bexar.org/DocumentCenter/View/12347/June-10-2017-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2019,
            election_date="2019-05-04",
            election_stage="general",
            election_name="May 4, 2019 Joint General, Special, and Charter Election",
            url="https://www.bexar.org/DocumentCenter/View/21819/May-4-2019-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2019,
            election_date="2019-06-08",
            election_stage="runoff",
            election_name="June 8, 2019 City of San Antonio Runoff Election",
            url="https://www.bexar.org/DocumentCenter/View/22149/June-8-2019-Media-Report",
            format="electionware-media-html",
        ),
        TexasMayorElectionFile(
            year=2021,
            election_date="2021-05-01",
            election_stage="general",
            election_name="May 1, 2021 Joint General, Special and Charter Election",
            url="https://www.bexar.org/DocumentCenter/View/30033/May-1-2021-Joint-General-Special-and-Charter-Election-Media-Report",
            format="electionware-summary-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2023,
            election_date="2023-05-06",
            election_stage="general",
            election_name="May 6, 2023 Joint General, Special, Charter and Bond Election",
            url="https://www.bexar.org/DocumentCenter/View/38278/May-6-2023-Joint-General---Official-Summary-Results-Report",
            format="electionware-summary-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2025,
            election_date="2025-05-03",
            election_stage="general",
            election_name="May 3, 2025 Joint General Special and Bond Election",
            url="https://www.bexar.org/DocumentCenter/View/48371/May-Summary-Precincts",
            format="electionware-precinct-csv",
        ),
        TexasMayorElectionFile(
            year=2025,
            election_date="2025-06-07",
            election_stage="runoff",
            election_name="City of San Antonio Runoff Election",
            url="https://www.bexar.org/DocumentCenter/View/48398",
            format="electionware-summary-pdf",
            quality_grade="B",
        ),
    ),
)


HOUSTON_SOURCE = TexasMayorSource(
    place="Houston",
    source_name="Houston official city/county election archives",
    homepage="https://www.houstontx.gov/citysec/elections/",
    url=None,
    county_portion_fips={"Harris County": "48201"},
    election_files=(
        TexasMayorElectionFile(
            year=1999,
            election_date="1999-11-02",
            election_stage="general",
            election_name="November 2, 1999 City of Houston General Election",
            url="https://houstontx.gov/citysec/elections/110299.pdf",
            format="houston-citysec-combined-pdf",
            quality_grade="B",
            county_portion_fips={
                "Harris County": "48201",
                "Fort Bend County": "48157",
                "Montgomery County": "48339",
            },
        ),
        TexasMayorElectionFile(
            year=2001,
            election_date="2001-11-06",
            election_stage="general",
            election_name="November 6, 2001 City of Houston General Election",
            url="https://houstontx.gov/citysec/elections/110601.pdf",
            format="houston-citysec-combined-pdf",
            quality_grade="B",
            county_portion_fips={
                "Harris County": "48201",
                "Fort Bend County": "48157",
                "Montgomery County": "48339",
            },
        ),
        TexasMayorElectionFile(
            year=2001,
            election_date="2001-12-01",
            election_stage="runoff",
            election_name="December 1, 2001 City of Houston Runoff Election",
            url="https://houstontx.gov/citysec/elections/120101.pdf",
            format="houston-citysec-combined-pdf",
            quality_grade="B",
            county_portion_fips={
                "Harris County": "48201",
                "Fort Bend County": "48157",
                "Montgomery County": "48339",
            },
        ),
        TexasMayorElectionFile(
            year=2003,
            election_date="2003-11-04",
            election_stage="general",
            election_name="November 4, 2003 City of Houston General Election",
            url="https://houstontx.gov/citysec/elections/110403.pdf",
            format="houston-citysec-combined-pdf",
            quality_grade="B",
            county_portion_fips={
                "Harris County": "48201",
                "Fort Bend County": "48157",
                "Montgomery County": "48339",
            },
        ),
        TexasMayorElectionFile(
            year=2005,
            election_date="2005-11-08",
            election_stage="general",
            election_name="November 8, 2005 City of Houston General Election",
            url="https://houstontx.gov/citysec/elections/110805.pdf",
            format="houston-citysec-combined-pdf",
            quality_grade="B",
            county_portion_fips={
                "Harris County": "48201",
                "Fort Bend County": "48157",
                "Montgomery County": "48339",
            },
        ),
        TexasMayorElectionFile(
            year=2007,
            election_date="2007-11-06",
            election_stage="general",
            election_name="November 6, 2007 City of Houston General Election",
            url="https://houstontx.gov/citysec/elections/110607.pdf",
            format="houston-citysec-combined-pdf",
            quality_grade="B",
            county_portion_fips={
                "Harris County": "48201",
                "Fort Bend County": "48157",
                "Montgomery County": "48339",
            },
        ),
        TexasMayorElectionFile(
            year=2009,
            election_date="2009-11-03",
            election_stage="general",
            election_name="November 3, 2009 Joint General and Special Elections",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/110309/Cumulative/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2009,
            election_date="2009-12-12",
            election_stage="runoff",
            election_name="December 12, 2009 Joint Runoff Election",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/121209/Cumulative/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2011,
            election_date="2011-11-08",
            election_stage="general",
            election_name="November 8, 2011 Joint Election",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/20111108/cumulative/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2013,
            election_date="2013-11-05",
            election_stage="general",
            election_name="November 5, 2013 Joint Election",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/20131105/cumulative/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2015,
            election_date="2015-11-03",
            election_stage="general",
            election_name="November 3, 2015 Joint General and Special Elections",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/20151103/cumulative/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2015,
            election_date="2015-12-12",
            election_stage="runoff",
            election_name="December 12, 2015 Joint Runoff Election",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/20151212/cumulative/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2019,
            election_date="2019-11-05",
            election_stage="general",
            election_name="November 5, 2019 Joint General and Special Elections",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/20191105/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2019,
            election_date="2019-12-14",
            election_stage="runoff",
            election_name="December 14, 2019 Joint Runoff Election",
            url="https://files.harrisvotes.com/harrisvotes/prd/HISTORY/20191214/cumulative.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2023,
            election_date="2023-11-07",
            election_stage="general",
            election_name="November 7, 2023 General and Special Elections",
            url="https://files.harrisvotes.com/harrisvotes/prd/Reports/Official-Cumulative-Results-11-14-2023_03-17-PM.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2023,
            election_date="2023-12-09",
            election_stage="runoff",
            election_name="December 9, 2023 Joint Runoff Election",
            url="https://files.harrisvotes.com/harrisvotes/prd/docs/Uploads/Official%20Cumulative%20Results-12-15-2023%2005-54-05%20PM.pdf",
            format="harris-cumulative-pdf",
            quality_grade="B",
        ),
    ),
)


AUSTIN_SOURCE = TexasMayorSource(
    place="Austin",
    source_name="City of Austin City Clerk canvass resolutions",
    homepage="https://www.austintexas.gov/department/city-clerk",
    url=None,
    county_portion_fips={
        "Travis County": "48453",
        "Williamson County": "48491",
        "Hays County": "48209",
    },
    election_files=(
        TexasMayorElectionFile(
            year=2022,
            election_date="2022-11-08",
            election_stage="general",
            election_name="November 8, 2022 City of Austin General Municipal Election",
            url="https://services.austintexas.gov/edims/document.cfm?id=397765",
            format="austin-resolution-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2022,
            election_date="2022-12-13",
            election_stage="runoff",
            election_name="December 13, 2022 City of Austin Runoff Election",
            url="https://services.austintexas.gov/edims/document.cfm?id=399837",
            format="austin-resolution-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2024,
            election_date="2024-11-05",
            election_stage="general",
            election_name="November 5, 2024 City of Austin General Municipal Election",
            url="https://services.austintexas.gov/edims/document.cfm?id=441389",
            format="austin-resolution-pdf",
            quality_grade="B",
        ),
    ),
)


DALLAS_SOURCE = TexasMayorSource(
    place="Dallas",
    source_name="City of Dallas City Secretary canvass resolutions",
    homepage="https://dallascityhall.com/government/citysecretary/elections/Pages/historical-data.aspx",
    url=None,
    county_portion_fips={
        "Dallas County": "48113",
        "Collin County": "48085",
        "Denton County": "48121",
        "Rockwall County": "48397",
        "Kaufman County": "48257",
    },
    election_files=(
        TexasMayorElectionFile(
            year=1981,
            election_date="1981-04-04",
            election_stage="general",
            election_name="April 4, 1981 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1983,
            election_date="1983-04-02",
            election_stage="general",
            election_name="April 2, 1983 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1985,
            election_date="1985-04-06",
            election_stage="general",
            election_name="April 6, 1985 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1987,
            election_date="1987-04-04",
            election_stage="general",
            election_name="April 4, 1987 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1987,
            election_date="1987-04-18",
            election_stage="runoff",
            election_name="April 18, 1987 City of Dallas Mayor Runoff Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1989,
            election_date="1989-05-06",
            election_stage="general",
            election_name="May 6, 1989 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1991,
            election_date="1991-11-05",
            election_stage="general",
            election_name="November 5, 1991 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1995,
            election_date="1995-05-06",
            election_stage="general",
            election_name="May 6, 1995 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=1999,
            election_date="1999-05-01",
            election_stage="general",
            election_name="May 1, 1999 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=2002,
            election_date="2002-01-19",
            election_stage="special",
            election_name="January 19, 2002 City of Dallas Special Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=2002,
            election_date="2002-02-16",
            election_stage="runoff",
            election_name="February 16, 2002 City of Dallas Special Runoff Election",
            url="https://citysecretary2.dallascityhall.com/pdf/Elections/electmasterlist.pdf",
            format="dallas-master-list-pdf",
            quality_grade="C",
        ),
        TexasMayorElectionFile(
            year=2007,
            election_date="2007-05-12",
            election_stage="general",
            election_name="May 12, 2007 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2007/05-23-07/07-1602.pdf",
            format="dallas-resolution-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2011,
            election_date="2011-05-14",
            election_stage="general",
            election_name="May 14, 2011 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2011/05-25-11/11-1386.pdf",
            format="dallas-resolution-ocr-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2011,
            election_date="2011-06-18",
            election_stage="runoff",
            election_name="June 18, 2011 City of Dallas Runoff Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2011/06-27-11/11-1900.pdf",
            format="dallas-resolution-ocr-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2015,
            election_date="2015-05-09",
            election_stage="general",
            election_name="May 9, 2015 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2015/05-20-15/15-0905.pdf",
            format="dallas-resolution-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2019,
            election_date="2019-05-04",
            election_stage="general",
            election_name="May 4, 2019 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2019/05-15-19/19-0735.pdf",
            format="dallas-resolution-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2019,
            election_date="2019-06-08",
            election_stage="runoff",
            election_name="June 8, 2019 City of Dallas Runoff Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2019/06-17-19/19-0955.pdf",
            format="dallas-resolution-pdf",
            quality_grade="B",
        ),
        TexasMayorElectionFile(
            year=2023,
            election_date="2023-05-06",
            election_stage="general",
            election_name="May 6, 2023 City of Dallas General Election",
            url="https://citysecretary2.dallascityhall.com/resolutions/2023/05-17-23/23-0665.pdf",
            format="dallas-resolution-pdf",
            quality_grade="B",
        ),
    ),
)


MAYOR_SOURCES = [FORT_WORTH_SOURCE, SAN_ANTONIO_SOURCE, HOUSTON_SOURCE, AUSTIN_SOURCE, DALLAS_SOURCE]
