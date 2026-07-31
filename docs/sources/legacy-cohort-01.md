# Legacy Cohort 01 Sources

This source-discovery record covers the first ten-state cohort for both legacy waves. Every year is explicitly registered as `source_identified`; none is marked imported until an official file is staged, parsed, reconciled, and tested.

| State | Official archive | Format lead | Years |
| --- | --- | --- | --- |
| Alabama (AL) | [https://www.sos.alabama.gov/alabama-votes/election-information/election-data](https://www.sos.alabama.gov/alabama-votes/election-information/election-data) | official PDF/HTML archive | 2000-2018 even-year generals |
| Alaska (AK) | [https://www.elections.alaska.gov/doc/info/ElectionResults.php](https://www.elections.alaska.gov/doc/info/ElectionResults.php) | official PDF/HTML archive | 2000-2018 even-year generals |
| Arizona (AZ) | [https://apps.azsos.gov/election/2010/General/ElectionInformation.htm](https://apps.azsos.gov/election/2010/General/ElectionInformation.htm) | cycle pages with official canvass PDF and precinct files | 2000-2018 even-year generals |
| Arkansas (AR) | [https://www.sos.arkansas.gov/elections/research/election-results](https://www.sos.arkansas.gov/elections/research/election-results) | official election-results archive | 2000-2018 even-year generals |
| Colorado (CO) | [https://www.sos.state.co.us/pubs/elections/Results/archive2000.html](https://www.sos.state.co.us/pubs/elections/Results/archive2000.html) | official PDF and precinct-level XLSX archive | 2000-2018 even-year generals |
| Connecticut (CT) | [https://portal.ct.gov/sots/election-services/statement-of-vote-pdfs/general-elections-statement-of-vote-1922](https://portal.ct.gov/sots/election-services/statement-of-vote-pdfs/general-elections-statement-of-vote-1922) | official Statement of Vote PDF archive | 2000-2018 even-year generals |
| Delaware (DE) | [https://elections.delaware.gov/elections/election_archive.html](https://elections.delaware.gov/elections/election_archive.html) | official raw-data and results archive | 2000-2018 even-year generals |
| Hawaii (HI) | [https://elections.hawaii.gov/election-result/2010-general-election/](https://elections.hawaii.gov/election-result/2010-general-election/) | official certified PDF and text reports | 2000-2018 even-year generals |
| Idaho (ID) | [https://sos.idaho.gov/elections-division/idaho-election-results/](https://sos.idaho.gov/elections-division/idaho-election-results/) | official statewide, county, and Excel archive | 2000-2018 even-year generals |
| Illinois (IL) | [https://www.elections.il.gov/PDFSiteMapProd.htm](https://www.elections.il.gov/PDFSiteMapProd.htm) | official downloadable vote-total and office CSV archive | 2000-2018 even-year generals |

## Processing Order

1. Stage official structured files first, especially Colorado, Delaware, Idaho, and Illinois downloadable tables.
2. Stage official PDF/HTML canvasses for Alabama, Alaska, Arizona, Arkansas, Connecticut, and Hawaii.
3. Record the election-cycle district schema before normalizing State Senate, State House, and U.S. House contests.
4. Use compiled data only after the official archive has been searched and the gap is documented in the source registry.
