# Texas Official Election Results Sources

Source pages:
- https://www.sos.state.tx.us/elections/historical/index.shtml
- https://www.sos.state.tx.us/elections/historical/elections-results-archive.shtml
- https://results.texas-election.com/reports

Downloaded files:
- `data/raw/texas/texas_2020_general_county_canvass.xlsx`
  - Source UI: Texas Election Results 2019-2024 portal, Reports, 2020 NOVEMBER 3RD GENERAL ELECTION, County by County Canvass Report, Excel.
  - Intended coverage: county-by-county official canvass for the 2020 general election.
  - Limitation noticed: workbook inspection found one sheet named `Voter Turnout Report` with only one populated cell, `ELECTION DATE-NAME`; the Excel export appears malformed or incomplete.
- `data/raw/texas/texas_2022_general_county_canvass.xlsx`
  - Source UI: Texas Election Results 2019-2024 portal, Reports, 2022 NOVEMBER 8TH GENERAL ELECTION, County by County Canvass Report, Excel.
  - Intended coverage: county-by-county official canvass for the 2022 general election.
  - Limitation noticed: workbook inspection found one sheet named `Voter Turnout Report` with only one populated cell, `ELECTION DATE-NAME`; the Excel export appears malformed or incomplete.
- `data/raw/texas/texas_2024_general_county_canvass.xlsx`
  - Source UI: Texas Election Results 2019-2024 portal, Reports, 2024 NOVEMBER 5TH GENERAL ELECTION, County by County Canvass Report, Excel.
  - Intended coverage: county-by-county official canvass for the 2024 general election.
  - Limitation noticed: workbook inspection found one sheet named `Voter Turnout Report` with only one populated cell, `ELECTION DATE-NAME`; the Excel export appears malformed or incomplete.
- `data/raw/texas/texas_2020_general_results_by_county.pdf`
  - Source UI: Texas Election Results 2019-2024 portal, Reports, 2020 NOVEMBER 3RD GENERAL ELECTION, County by County Canvass Report, PDF.
  - Appears to cover: county-by-county official canvass for the 2020 general election, including President, U.S. Senate, U.S. House, State Senate, and State House.
  - Import status: President, U.S. Senate, U.S. House, State Senate, and State House contests are imported by `npm run texas:generate`.
- `data/raw/texas/texas_2022_general_results_by_county.pdf`
  - Source UI: Texas Election Results 2019-2024 portal, Reports, 2022 NOVEMBER 8TH GENERAL ELECTION, County by County Canvass Report, PDF.
  - Appears to cover: county-by-county official canvass for the 2022 general election, including Governor, U.S. House, State Senate, and State House.
  - Import status: Governor, U.S. House, State Senate, and State House contests are imported by `npm run texas:generate`.
- `data/raw/texas/texas_2024_general_results_by_county.pdf`
  - Source UI: Texas Election Results 2019-2024 portal, Reports, 2024 NOVEMBER 5TH GENERAL ELECTION, County by County Canvass Report, PDF.
  - Appears to cover: county-by-county official canvass for the 2024 general election, including President, U.S. Senate, U.S. House, State Senate, and State House.
  - Import status: President, U.S. Senate, U.S. House, State Senate, and State House contests are imported by `npm run texas:generate`.

Access notes:
- Direct terminal requests to Texas SOS pages failed from the sandbox.
- Browser access to the Texas portal worked, including election selection for 2020, 2022, and 2024.
- The portal-generated Excel workbooks downloaded, but local inspection indicates the files are not usable candidate-result exports.
