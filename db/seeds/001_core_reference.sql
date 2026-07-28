INSERT INTO parties (name, short_name, canonical_code, wikidata_id, color_hex) VALUES
  ('Democratic Party', 'Dem', 'DEMOCRAT', NULL, '#2563eb'),
  ('Republican Party', 'Rep', 'REPUBLICAN', NULL, '#dc2626'),
  ('Libertarian Party', 'Lib', 'LIBERTARIAN', NULL, '#ca8a04'),
  ('Green Party', 'Green', 'GREEN', NULL, '#16a34a'),
  ('Other', 'Other', 'OTHER', NULL, '#6b7280'),
  ('Nonpartisan', 'NP', 'NONPARTISAN', NULL, '#737373')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  short_name = VALUES(short_name),
  wikidata_id = VALUES(wikidata_id),
  color_hex = VALUES(color_hex);

INSERT INTO offices (name, level, body, wikidata_id, districted, executive) VALUES
  ('President', 'federal', 'Executive', NULL, FALSE, TRUE),
  ('U.S. Senate', 'federal', 'Congress', NULL, FALSE, FALSE),
  ('U.S. House', 'federal', 'Congress', NULL, TRUE, FALSE),
  ('Governor', 'state', 'Executive', NULL, FALSE, TRUE),
  ('State Senate', 'state', 'Legislature', NULL, TRUE, FALSE),
  ('State House', 'state', 'Legislature', NULL, TRUE, FALSE),
  ('Mayor', 'local', 'Executive', NULL, FALSE, TRUE)
ON DUPLICATE KEY UPDATE
  body = VALUES(body),
  wikidata_id = VALUES(wikidata_id),
  districted = VALUES(districted),
  executive = VALUES(executive);

INSERT INTO jurisdictions (type, name, state_po, fips, official_id, wikidata_id, parent_jurisdiction_id, valid_from, valid_to, notes) VALUES
  ('country', 'United States', NULL, '00', 'US', NULL, NULL, NULL, NULL, NULL)
ON DUPLICATE KEY UPDATE
  official_id = VALUES(official_id),
  wikidata_id = VALUES(wikidata_id),
  notes = VALUES(notes);

INSERT INTO jurisdictions (type, name, state_po, fips, official_id, wikidata_id, parent_jurisdiction_id, valid_from, valid_to, notes) VALUES
  ('state', 'Florida', 'FL', '12', 'FL', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'country' AND official_id = 'US') AS parent), NULL, NULL, 'Pilot state'),
  ('state', 'California', 'CA', '06', 'CA', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'country' AND official_id = 'US') AS parent), NULL, NULL, 'Pilot state'),
  ('state', 'Pennsylvania', 'PA', '42', 'PA', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'country' AND official_id = 'US') AS parent), NULL, NULL, 'Pilot state'),
  ('state', 'Texas', 'TX', '48', 'TX', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'country' AND official_id = 'US') AS parent), NULL, NULL, 'Pilot state'),
  ('state', 'Ohio', 'OH', '39', 'OH', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'country' AND official_id = 'US') AS parent), NULL, NULL, 'Pilot state')
ON DUPLICATE KEY UPDATE
  fips = VALUES(fips),
  official_id = VALUES(official_id),
  wikidata_id = VALUES(wikidata_id),
  parent_jurisdiction_id = VALUES(parent_jurisdiction_id),
  notes = VALUES(notes);

INSERT INTO jurisdictions (type, name, state_po, fips, official_id, wikidata_id, parent_jurisdiction_id, valid_from, valid_to, notes) VALUES
  ('city', 'Miami', 'FL', NULL, 'FL-MIAMI', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'FL') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Jacksonville', 'FL', NULL, 'FL-JACKSONVILLE', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'FL') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Tampa', 'FL', NULL, 'FL-TAMPA', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'FL') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Orlando', 'FL', NULL, 'FL-ORLANDO', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'FL') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Los Angeles', 'CA', NULL, 'CA-LOS-ANGELES', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'CA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'San Francisco', 'CA', NULL, 'CA-SAN-FRANCISCO', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'CA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'San Diego', 'CA', NULL, 'CA-SAN-DIEGO', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'CA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'San Jose', 'CA', NULL, 'CA-SAN-JOSE', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'CA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Sacramento', 'CA', NULL, 'CA-SACRAMENTO', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'CA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Philadelphia', 'PA', NULL, 'PA-PHILADELPHIA', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'PA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Pittsburgh', 'PA', NULL, 'PA-PITTSBURGH', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'PA') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Houston', 'TX', NULL, 'TX-HOUSTON', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'TX') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Dallas', 'TX', NULL, 'TX-DALLAS', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'TX') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Austin', 'TX', NULL, 'TX-AUSTIN', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'TX') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'San Antonio', 'TX', NULL, 'TX-SAN-ANTONIO', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'TX') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Fort Worth', 'TX', NULL, 'TX-FORT-WORTH', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'TX') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Columbus', 'OH', NULL, 'OH-COLUMBUS', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'OH') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Cleveland', 'OH', NULL, 'OH-CLEVELAND', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'OH') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Cincinnati', 'OH', NULL, 'OH-CINCINNATI', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'OH') AS parent), NULL, NULL, 'Pilot mayor city'),
  ('city', 'Toledo', 'OH', NULL, 'OH-TOLEDO', NULL, (SELECT id FROM (SELECT id FROM jurisdictions WHERE type = 'state' AND state_po = 'OH') AS parent), NULL, NULL, 'Pilot mayor city')
ON DUPLICATE KEY UPDATE
  wikidata_id = VALUES(wikidata_id),
  parent_jurisdiction_id = VALUES(parent_jurisdiction_id),
  notes = VALUES(notes);

INSERT INTO sources (name, source_type, homepage_url, discovery_reference_url, license_name, license_url, notes) VALUES
  ('Princeton University Library Elections and Voting Data Guide', 'reference_guide', 'https://libguides.princeton.edu/elections', NULL, NULL, NULL, 'Source discovery reference; not a vote-total source.'),
  ('Wikipedia List of United States official election results by state', 'reference_guide', 'https://en.wikipedia.org/wiki/List_of_United_States_official_election_results_by_state', NULL, NULL, NULL, 'Source discovery reference; follow links to official result files where available.'),
  ('MIT Election Data and Science Lab', 'compiled_dataset', 'https://electionlab.mit.edu/data', 'https://libguides.princeton.edu/elections', 'CC0 1.0', 'http://creativecommons.org/publicdomain/zero/1.0', 'Compiled election returns source used for the initial county presidential dataset.')
ON DUPLICATE KEY UPDATE
  source_type = VALUES(source_type),
  homepage_url = VALUES(homepage_url),
  discovery_reference_url = VALUES(discovery_reference_url),
  license_name = VALUES(license_name),
  license_url = VALUES(license_url),
  notes = VALUES(notes);

INSERT IGNORE INTO migration_versions (name) VALUES ('seed_001_core_reference.sql');
