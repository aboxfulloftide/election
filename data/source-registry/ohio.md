# Ohio Official Election Results Sources

Source pages:
- https://www.ohiosos.gov/data
- https://data.ohiosos.gov/portal/election-dashboards
- https://data.ohiosos.gov/portal/past-election-results
- https://ohio.gov/wps/portal/gov/site/government/resources/election-results

Downloaded files:
- `data/raw/ohio/ohio_2020_general_statewide_results_by_county.xlsx`
  - Source URL: https://publicfiles.ohiosos.gov/election-results/past-elections/2020/General%20Election:%20November%203,%202020/group1/statewideresultsbycounty.xlsx
  - Source UI: Ohio Data Portal, Past Election Results, 2020, General Election: November 3, 2020, first Results by County card.
  - Appears to cover: November 3, 2020 General Election Official Canvass; sheets include `Master`, `President and Vice President`, `U.S. Congress`, `Ohio General Assembly`, `State Board of Education`, and `Judicial`.
  - Limitations noticed: no Governor or U.S. Senate contests in 2020 general; workbook is structured XLSX.
- `data/raw/ohio/ohio_2022_general_county_races_summary_partial.xlsx`
  - Source URL: https://publicfiles.ohiosos.gov/election-results/past-elections/2022/General%20Election:%20November%208,%202022/group2/county-races-summary.xlsx
  - Source UI: Ohio Data Portal, Past Election Results, 2022, General Election: November 8, 2022, County Races Summary card.
  - Appears to cover: November 8, 2022 General Election Official Canvass for county officials; sheets include `Master`, `County Commissioner`, `County Auditor`, `Prosecuting Attorney`, `Clerk of the Court of Common Pleas`, `Sheriff`, and other county offices.
  - Limitations noticed: this is a partial fallback. The desired 2022 `Statewide Races Summary` card is the one described by the portal as covering Statewide Offices, U.S. Senate, U.S. Representatives to Congress, and General Assembly, but repeated browser attempts did not produce that workbook in this session.
- `data/raw/ohio/ohio_2022_general_statewide_races_summary.xlsx`
  - Source URL: https://publicfiles.ohiosos.gov/election-results/past-elections/2022/General%20Election:%20November%208,%202022/group1/statewide-races-summary.xlsx
  - Source UI: Ohio Data Portal, Past Election Results, 2022, General Election: November 8, 2022, Statewide Races Summary card.
  - Appears to cover: November 8, 2022 General Election Official Canvass; sheets include `Master`, `Statewide Offices`, `Supreme Court`, `U.S. Congress`, `General Assembly`, `Judicial`, and `State Board of Education`.
  - Limitations noticed: workbook is structured XLSX and is imported; the separate county-races file remains local-office-only.
- `data/raw/ohio/ohio_2024_general_statewide_results_by_county.xlsx`
  - Source URL: https://publicfiles.ohiosos.gov/election-results/past-elections/2024/General%20Election:%20November%205,%202024/group1/statewide-race-summary.xlsx
  - Source UI: Ohio Data Portal, Past Election Results, 2024, General Election: November 5, 2024, first Results by County card.
  - Appears to cover: November 5, 2024 General Election Official Canvass; sheets include `Master`, `President and Vice President`, `Justice of the Supreme Court`, `U.S. Congress`, `General Assembly`, `Judge of Court of Appeals`, and `State Board of Education`.
  - Limitations noticed: no Governor contest in 2024 general; U.S. Senate appears in the `U.S. Congress` sheet.

Access notes:
- Direct terminal requests to Ohio dashboard and public file endpoints failed or returned access/maintenance responses from the sandbox.
- Browser access to the Ohio Data Portal worked.
- Browser download events were unreliable for Ohio; successful file source URLs were recovered from Windows `Zone.Identifier` metadata.
