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
  supplemental?: boolean;
  supplemental_count?: number;
  official_count?: number;
  county_count?: number;
  source_name?: string;
  source_url?: string;
  quality_grade?: string;
  official?: boolean;
};

export type CountySummary = {
  fips: string;
  fips_aliases?: string[];
  state: string;
  state_po: string;
  county_name: string;
  previous_names?: string[];
  valid_from_year?: number;
  valid_to_year?: number;
  inactive_reason?: string;
  geography_note?: string;
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
    quality_grade?: string;
    supplements?: Array<{
      name: string;
      url: string;
      years: number[];
      license: string;
      quality_grade: string;
      notes: string;
    }>;
    official_state_sources?: Array<{
      name: string;
      url: string;
      state_po: string;
      years: number[];
      quality_grade: string;
      notes: string;
    }>;
  };
  years: number[];
  counties: CountySummary[];
};

export type CandidateResult = {
  candidate: string;
  party: Party;
  votes: number;
};

export type FloridaContestCounty = {
  fips: string;
  county_name: string;
  total_votes: number;
  winner: CandidateResult;
  margin_votes: number;
  candidates: CandidateResult[];
};

export type FloridaPrecinctRecord = {
  precinct_id: string;
  total_votes: number;
  winner: CandidateResult | null;
  margin_votes: number;
  candidates: CandidateResult[];
};

export type FloridaPrecinctContest = {
  contest_id: number;
  office: string;
  district_label?: string | null;
  name: string;
  precincts: FloridaPrecinctRecord[];
};

export type FloridaPrecinctBundle = {
  source: {
    name: string;
    url: string;
    source_file_url?: string | null;
    retrieved_at: string;
    quality_grade: string;
  };
  election: {
    year: number;
    date: string;
    type: string;
    state: string;
  };
  county: {
    fips: string;
    name: string;
  };
  geometry: {
    layer_key: string;
    geometry_url: string;
    feature_count: number;
    vintage: string;
    result_precinct_count?: number;
    matched_result_precinct_count?: number;
    unmatched_result_precinct_count?: number;
    file_size_bytes?: number;
  };
  contests: FloridaPrecinctContest[];
};

export type FloridaPrecinctCatalogEntry = {
  year: number;
  county_fips: string;
  county_name: string;
  bundle_url: string;
  geometry_layer_key: string;
  quality_grade: string;
  map_ready: boolean;
};

export type FloridaPrecinctCatalog = {
  bundles: FloridaPrecinctCatalogEntry[];
};

export type FloridaContest = {
  contest_id: number;
  office: "President" | "U.S. Senate" | "U.S. House" | "Governor" | "State Senate" | "State House" | string;
  district_label?: string | null;
  name: string;
  state: string;
  state_po: "FL" | "CA";
  total_votes: number;
  winner: CandidateResult;
  margin_votes: number;
  candidates: CandidateResult[];
  counties: FloridaContestCounty[];
};

export type FloridaStatewideElection = {
  source: {
    name: string;
    url: string;
    source_file_url?: string | null;
    retrieved_at: string;
    quality_grade: string;
  };
  election: {
    year: number;
    date: string;
    type: string;
    state: string;
  };
  contests: FloridaContest[];
};

export type FloridaStatewideSummary = {
  source: {
    name: string;
    url: string;
    retrieved_at: string;
    quality_grade: string;
  };
  elections: FloridaStatewideElection[];
};

export type FloridaDistrictCounty = {
  fips: string;
  county_name: string;
  total_votes: number;
  winner: CandidateResult;
  margin_votes: number;
  candidates: CandidateResult[];
};

export type FloridaDistrictContest = {
  contest_id: number;
  name: string;
  office: "U.S. House" | "State Senate" | "State House" | string;
  district_label: string;
  district_number: number;
  geometry_id: number;
  geometry_official_id: string;
  total_votes: number;
  winner: CandidateResult;
  margin_votes: number;
  candidates: CandidateResult[];
  counties: FloridaDistrictCounty[];
};

export type FloridaDistrictLayer = {
  layer_key: string;
  office: "U.S. House" | "State Senate" | "State House" | string;
  geo_type: string;
  geometry_url: string;
  feature_count: number;
  contest_count: number;
  contests: FloridaDistrictContest[];
};

export type FloridaDistrictElection = {
  source: {
    name: string;
    url: string;
    source_file_url?: string | null;
    retrieved_at: string;
    quality_grade: string;
  };
  election: {
    year: number;
    date: string;
    type: string;
    state: string;
  };
  state: string;
  state_po: "FL" | "CA";
  layers: FloridaDistrictLayer[];
};

export type FloridaDistrictDrilldown = {
  source: {
    name: string;
    url: string;
    retrieved_at: string;
    quality_grade: string;
  };
  state: string;
  state_po: "FL" | "CA";
  elections: FloridaDistrictElection[];
};
