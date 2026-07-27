export type Party = "DEMOCRAT" | "REPUBLICAN" | "LIBERTARIAN" | "GREEN" | "OTHER" | string;

export type CountyResult = {
  totalvotes: number;
  parties: Record<Party, number>;
  winner_party: Party;
  winner_votes: number;
  margin_votes: number;
  margin_pct: number;
  dem_share: number;
  rep_share: number;
  two_party_margin: number;
};

export type CountySummary = {
  fips: string;
  state: string;
  state_po: string;
  county_name: string;
  results: Record<string, CountyResult>;
};

export type ElectionSummary = {
  source: {
    name: string;
    doi: string;
    url: string;
    retrieved_at: string;
    dataverse_version: string;
    dataverse_release_time: string;
    license: string;
  };
  years: number[];
  counties: CountySummary[];
};

