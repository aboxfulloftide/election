CREATE TABLE IF NOT EXISTS jurisdiction_aliases (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  jurisdiction_id BIGINT UNSIGNED NOT NULL,
  alias_type ENUM('fips', 'name', 'official_id') NOT NULL,
  alias_value VARCHAR(255) NOT NULL,
  valid_from SMALLINT UNSIGNED NULL,
  valid_to SMALLINT UNSIGNED NULL,
  source_file_id BIGINT UNSIGNED NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_jurisdiction_aliases (alias_type, alias_value, valid_from, valid_to),
  KEY idx_jurisdiction_aliases_jurisdiction (jurisdiction_id),
  KEY idx_jurisdiction_aliases_value (alias_type, alias_value),
  KEY idx_jurisdiction_aliases_source_file (source_file_id),
  CONSTRAINT fk_jurisdiction_aliases_jurisdiction FOREIGN KEY (jurisdiction_id) REFERENCES jurisdictions (id),
  CONSTRAINT fk_jurisdiction_aliases_source_file FOREIGN KEY (source_file_id) REFERENCES source_files (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO migration_versions (name) VALUES ('003_jurisdiction_aliases.sql');
