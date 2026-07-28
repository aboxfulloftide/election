CREATE TABLE IF NOT EXISTS migration_versions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_migration_versions_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS sources (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  source_type ENUM('official_state', 'official_county', 'official_city', 'compiled_dataset', 'archive', 'reference_guide', 'other') NOT NULL,
  homepage_url TEXT NULL,
  discovery_reference_url TEXT NULL,
  license_name VARCHAR(255) NULL,
  license_url TEXT NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sources_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS source_files (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  source_id BIGINT UNSIGNED NOT NULL,
  url TEXT NULL,
  local_path TEXT NULL,
  discovery_reference_url TEXT NULL,
  retrieved_at DATETIME NOT NULL,
  file_name VARCHAR(255) NULL,
  file_type VARCHAR(80) NULL,
  checksum_sha256 CHAR(64) NULL,
  covers_year_start SMALLINT UNSIGNED NULL,
  covers_year_end SMALLINT UNSIGNED NULL,
  raw_license_text TEXT NULL,
  transform_notes TEXT NULL,
  quality_grade ENUM('A', 'B', 'C', 'D') NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_source_files_source_id (source_id),
  KEY idx_source_files_checksum (checksum_sha256),
  CONSTRAINT fk_source_files_source FOREIGN KEY (source_id) REFERENCES sources (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS elections (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  year SMALLINT UNSIGNED NOT NULL,
  election_date DATE NULL,
  election_type ENUM('general', 'runoff') NOT NULL,
  name VARCHAR(255) NOT NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_elections_year_type_date (year, election_type, election_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS jurisdictions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  type ENUM('country', 'state', 'county', 'city', 'district', 'precinct') NOT NULL,
  name VARCHAR(255) NOT NULL,
  state_po CHAR(2) NULL,
  fips VARCHAR(20) NULL,
  official_id VARCHAR(100) NULL,
  wikidata_id VARCHAR(40) NULL,
  parent_jurisdiction_id BIGINT UNSIGNED NULL,
  valid_from SMALLINT UNSIGNED NULL,
  valid_to SMALLINT UNSIGNED NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_jurisdictions_type_official_id (type, official_id),
  KEY idx_jurisdictions_type_state (type, state_po),
  KEY idx_jurisdictions_fips (fips),
  KEY idx_jurisdictions_parent (parent_jurisdiction_id),
  CONSTRAINT fk_jurisdictions_parent FOREIGN KEY (parent_jurisdiction_id) REFERENCES jurisdictions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS offices (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  level ENUM('federal', 'state', 'local') NOT NULL,
  body VARCHAR(120) NULL,
  wikidata_id VARCHAR(40) NULL,
  districted BOOLEAN NOT NULL DEFAULT FALSE,
  executive BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_offices_name_level_body (name, level, body)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS parties (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  short_name VARCHAR(40) NOT NULL,
  canonical_code VARCHAR(40) NOT NULL,
  wikidata_id VARCHAR(40) NULL,
  color_hex CHAR(7) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_parties_canonical_code (canonical_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS candidates (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  display_name VARCHAR(255) NOT NULL,
  first_name VARCHAR(120) NULL,
  last_name VARCHAR(120) NULL,
  normalized_name VARCHAR(255) NOT NULL,
  wikidata_id VARCHAR(40) NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_candidates_normalized_name (normalized_name),
  KEY idx_candidates_wikidata_id (wikidata_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS contests (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  election_id BIGINT UNSIGNED NOT NULL,
  office_id BIGINT UNSIGNED NOT NULL,
  contest_jurisdiction_id BIGINT UNSIGNED NOT NULL,
  district_label VARCHAR(100) NULL,
  seat_label VARCHAR(100) NULL,
  is_special BOOLEAN NOT NULL DEFAULT FALSE,
  is_runoff BOOLEAN NOT NULL DEFAULT FALSE,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_contests_election (election_id),
  KEY idx_contests_office (office_id),
  KEY idx_contests_jurisdiction (contest_jurisdiction_id),
  CONSTRAINT fk_contests_election FOREIGN KEY (election_id) REFERENCES elections (id),
  CONSTRAINT fk_contests_office FOREIGN KEY (office_id) REFERENCES offices (id),
  CONSTRAINT fk_contests_jurisdiction FOREIGN KEY (contest_jurisdiction_id) REFERENCES jurisdictions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS contest_candidates (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  contest_id BIGINT UNSIGNED NOT NULL,
  candidate_id BIGINT UNSIGNED NOT NULL,
  party_id BIGINT UNSIGNED NULL,
  ballot_label VARCHAR(255) NULL,
  incumbent BOOLEAN NULL,
  winner BOOLEAN NULL,
  source_id BIGINT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_contest_candidates (contest_id, candidate_id, party_id),
  KEY idx_contest_candidates_candidate (candidate_id),
  KEY idx_contest_candidates_party (party_id),
  KEY idx_contest_candidates_source (source_id),
  CONSTRAINT fk_contest_candidates_contest FOREIGN KEY (contest_id) REFERENCES contests (id),
  CONSTRAINT fk_contest_candidates_candidate FOREIGN KEY (candidate_id) REFERENCES candidates (id),
  CONSTRAINT fk_contest_candidates_party FOREIGN KEY (party_id) REFERENCES parties (id),
  CONSTRAINT fk_contest_candidates_source FOREIGN KEY (source_id) REFERENCES sources (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS reporting_units (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  jurisdiction_id BIGINT UNSIGNED NOT NULL,
  unit_type ENUM('state', 'county', 'county_district', 'district', 'city', 'precinct') NOT NULL,
  name VARCHAR(255) NOT NULL,
  state_po CHAR(2) NULL,
  county_fips VARCHAR(10) NULL,
  precinct_code VARCHAR(100) NULL,
  district_label VARCHAR(100) NULL,
  valid_from SMALLINT UNSIGNED NULL,
  valid_to SMALLINT UNSIGNED NULL,
  geometry_id BIGINT UNSIGNED NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_reporting_units_jurisdiction (jurisdiction_id),
  KEY idx_reporting_units_type_state (unit_type, state_po),
  KEY idx_reporting_units_county_fips (county_fips),
  CONSTRAINT fk_reporting_units_jurisdiction FOREIGN KEY (jurisdiction_id) REFERENCES jurisdictions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS results (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  contest_id BIGINT UNSIGNED NOT NULL,
  contest_candidate_id BIGINT UNSIGNED NOT NULL,
  reporting_unit_id BIGINT UNSIGNED NOT NULL,
  votes INT UNSIGNED NOT NULL,
  total_votes INT UNSIGNED NULL,
  vote_mode VARCHAR(80) NOT NULL DEFAULT 'total',
  source_file_id BIGINT UNSIGNED NOT NULL,
  quality_grade ENUM('A', 'B', 'C', 'D') NOT NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_results_candidate_unit_mode_source (contest_id, contest_candidate_id, reporting_unit_id, vote_mode, source_file_id),
  KEY idx_results_contest (contest_id),
  KEY idx_results_reporting_unit (reporting_unit_id),
  KEY idx_results_source_file (source_file_id),
  CONSTRAINT fk_results_contest FOREIGN KEY (contest_id) REFERENCES contests (id),
  CONSTRAINT fk_results_contest_candidate FOREIGN KEY (contest_candidate_id) REFERENCES contest_candidates (id),
  CONSTRAINT fk_results_reporting_unit FOREIGN KEY (reporting_unit_id) REFERENCES reporting_units (id),
  CONSTRAINT fk_results_source_file FOREIGN KEY (source_file_id) REFERENCES source_files (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS data_quality_notes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  entity_type ENUM('source', 'source_file', 'election', 'contest', 'reporting_unit', 'result') NOT NULL,
  entity_id BIGINT UNSIGNED NOT NULL,
  severity ENUM('info', 'warning', 'error') NOT NULL DEFAULT 'info',
  note TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_data_quality_notes_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO migration_versions (name) VALUES ('001_initial_schema.sql');
