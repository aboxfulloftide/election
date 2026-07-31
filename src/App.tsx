import { useEffect, useMemo, useState } from "react";
import { geoAlbersUsa, geoMercator, geoPath } from "d3-geo";
import { max, rollup, sum } from "d3-array";
import { scaleThreshold } from "d3-scale";
import { feature, mesh } from "topojson-client";
import { ChevronDown, GitCompareArrows, Map as MapIcon, MapPinned, RadioTower } from "lucide-react";
import type { GeometryCollection, Topology } from "topojson-specification";
import us from "us-atlas/counties-10m.json";
import type {
  CandidateResult,
  CountyResult,
  CountySummary,
  ElectionSummary,
  FloridaContest,
  FloridaContestCounty,
  FloridaPrecinctBundle,
  FloridaPrecinctCatalog,
  FloridaPrecinctCatalogEntry,
  FloridaPrecinctContest,
  FloridaPrecinctRecord,
  FloridaDistrictContest,
  FloridaDistrictDrilldown,
  FloridaDistrictElection,
  FloridaDistrictLayer,
  FloridaStatewideElection,
  FloridaStatewideSummary,
} from "./types";

type Metric = "winner" | "shift";
type ViewMode = "national" | "official";
type OfficialStatePo = "CA" | "FL";
type CountyFeature = GeoJSON.Feature<GeoJSON.Geometry, GeoJSON.GeoJsonProperties> & { id?: string | number };
type DistrictFeature = GeoJSON.Feature<GeoJSON.MultiPolygon, GeoJSON.GeoJsonProperties> & { id?: string | number };
type DistrictFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.MultiPolygon, GeoJSON.GeoJsonProperties>;
type PrecinctFeature = GeoJSON.Feature<GeoJSON.MultiPolygon, GeoJSON.GeoJsonProperties> & { id?: string | number };
type PrecinctFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.MultiPolygon, GeoJSON.GeoJsonProperties>;
type SelectOption = string | { value: string; label: string };
type AggregateDetail = {
  scope: "country" | "state";
  name: string;
  statePo?: string;
};
type UsTopology = Topology<{
  counties: GeometryCollection;
  states: GeometryCollection;
}>;

const partyLabels: Record<string, string> = {
  DEMOCRAT: "Dem",
  REPUBLICAN: "Rep",
  LIBERTARIAN: "Lib",
  GREEN: "Grn",
  NONPARTISAN: "NP",
  OTHER: "Other",
};

const stateFipsPrefixes: Record<string, string> = {
  CA: "06",
  FL: "12",
};

const officialSourceLabels: Record<string, string> = {
  CA: "California Secretary of State Statement of Vote",
  FL: "Florida Division of Elections precinct returns",
};

const officialStateOptions: Array<{ value: OfficialStatePo; label: string }> = [
  { value: "FL", label: "Florida" },
  { value: "CA", label: "California" },
];

const winnerScale = scaleThreshold<number, string>()
  .domain([-60, -40, -20, -10, 0, 10, 20, 40, 60])
  .range(["#7f1d1d", "#b91c1c", "#ef4444", "#fca5a5", "#e5e7eb", "#93c5fd", "#3b82f6", "#1d4ed8", "#1e3a8a", "#172554"]);

const shiftScale = scaleThreshold<number, string>()
  .domain([-30, -15, -7.5, -2.5, 2.5, 7.5, 15, 30])
  .range(["#7f1d1d", "#b91c1c", "#ef4444", "#fecaca", "#e5e7eb", "#bfdbfe", "#60a5fa", "#2563eb", "#1e3a8a"]);

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatBytes(value: number | undefined) {
  if (value === undefined) return "Unknown";
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(0)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatPct(value: number) {
  return `${Math.abs(value).toFixed(1)}%`;
}

function formatSignedNumber(value: number) {
  const sign = value >= 0 ? "+" : "-";
  return `${sign}${formatNumber(Math.abs(value))}`;
}

function partyColor(party: string) {
  if (party === "DEMOCRAT") return "#2563eb";
  if (party === "REPUBLICAN") return "#dc2626";
  if (party === "LIBERTARIAN") return "#ca8a04";
  if (party === "GREEN") return "#16a34a";
  if (party === "NONPARTISAN") return "#a3a3a3";
  return "#6b7280";
}

function resultMargin(result: CountyResult | undefined) {
  if (!result) return 0;
  return result.two_party_margin;
}

function mapColor(result: CountyResult | undefined, previous: CountyResult | undefined, metric: Metric) {
  if (!result) return "#d4d4d8";
  if (metric === "shift") {
    if (!previous) return "#71717a";
    return shiftScale(resultMargin(result) - resultMargin(previous));
  }
  return winnerScale(resultMargin(result));
}

function resultLeader(result: CountyResult | undefined) {
  if (!result) return "No data";
  const leader = partyLabels[result.winner_party] ?? result.winner_party;
  return `${leader} +${formatPct(result.margin_pct)}`;
}

function signedContestMargin(contest: FloridaDistrictContest | FloridaContest | undefined) {
  if (!contest || contest.total_votes === 0) return 0;
  const demVotes = contest.candidates.find((candidate) => candidate.party === "DEMOCRAT")?.votes ?? 0;
  const repVotes = contest.candidates.find((candidate) => candidate.party === "REPUBLICAN")?.votes ?? 0;
  if (demVotes || repVotes) return ((demVotes - repVotes) / contest.total_votes) * 100;
  const winnerSign = contest.winner.party === "REPUBLICAN" ? -1 : 1;
  return winnerSign * (contest.margin_votes / contest.total_votes) * 100;
}

function contestColor(contest: FloridaDistrictContest | FloridaContest | undefined) {
  if (!contest) return "#3f3f46";
  return winnerScale(signedContestMargin(contest));
}

function districtColor(contest: FloridaDistrictContest | undefined, previous: FloridaDistrictContest | undefined, metric: Metric) {
  if (!contest) return "#3f3f46";
  if (metric === "shift") {
    if (!previous) return "#71717a";
    return shiftScale(signedContestMargin(contest) - signedContestMargin(previous));
  }
  return contestColor(contest);
}

function contestLeader(contest: FloridaDistrictContest | FloridaContest | undefined) {
  if (!contest) return "No contest";
  const leader = partyLabels[contest.winner.party] ?? contest.winner.party;
  const marginPct = contest.total_votes ? (contest.margin_votes / contest.total_votes) * 100 : 0;
  return `${leader} +${formatPct(marginPct)}`;
}

function candidateVotesByParty(candidates: CandidateResult[]) {
  const map = new Map<string, number>();
  for (const candidate of candidates) {
    map.set(candidate.party, (map.get(candidate.party) ?? 0) + candidate.votes);
  }
  return map;
}

function comparisonClass(value: number, party?: string) {
  if (party === "REPUBLICAN") return value >= 0 ? "rep-text" : "dem-text";
  if (party === "DEMOCRAT") return value >= 0 ? "dem-text" : "rep-text";
  return "";
}

function ComparisonTable({
  currentLabel,
  compareLabel,
  rows,
}: {
  currentLabel: string;
  compareLabel: string;
  rows: Array<{ label: string; party?: string; current: number; compare: number | null }>;
}) {
  return (
    <div className="comparison-table">
      <div className="comparison-head">
        <span>Votes</span>
        <b>{currentLabel}</b>
        <b>{compareLabel}</b>
        <b>+/-</b>
      </div>
      {rows.map((row) => {
        const change = row.compare === null ? null : row.current - row.compare;
        return (
          <div className="comparison-row" key={row.label}>
            <span style={row.party ? { color: partyColor(row.party) } : undefined}>{row.label}</span>
            <b>{formatNumber(row.current)}</b>
            <b>{row.compare === null ? "N/A" : formatNumber(row.compare)}</b>
            <b className={change === null ? undefined : comparisonClass(change, row.party)}>{change === null ? "N/A" : formatSignedNumber(change)}</b>
          </div>
        );
      })}
    </div>
  );
}

function aggregateCountyResults(counties: CountySummary[], year: string): CountyResult | undefined {
  const parties: Record<string, number> = {};
  let totalvotes = 0;
  let countyCount = 0;
  let supplementalCount = 0;
  let officialCount = 0;
  for (const county of counties) {
    const result = county.results[year];
    if (!result) continue;
    countyCount += 1;
    if (result.supplemental) supplementalCount += 1;
    if (result.official) officialCount += 1;
    totalvotes += result.totalvotes;
    for (const [party, votes] of Object.entries(result.parties)) {
      parties[party] = (parties[party] ?? 0) + votes;
    }
  }
  if (totalvotes === 0) return undefined;
  const ordered = Object.entries(parties).sort((a, b) => b[1] - a[1]);
  const [winnerParty, winnerVotes] = ordered[0] ?? ["OTHER", 0];
  const runnerUpVotes = ordered[1]?.[1] ?? 0;
  const demVotes = parties.DEMOCRAT ?? 0;
  const repVotes = parties.REPUBLICAN ?? 0;
  const marginVotes = winnerVotes - runnerUpVotes;
  return {
    totalvotes,
    parties,
    winner_party: winnerParty,
    winner_votes: winnerVotes,
    margin_votes: marginVotes,
    margin_pct: totalvotes ? (marginVotes / totalvotes) * 100 : 0,
    dem_share: totalvotes ? (demVotes / totalvotes) * 100 : 0,
    rep_share: totalvotes ? (repVotes / totalvotes) * 100 : 0,
    two_party_margin: totalvotes ? ((demVotes - repVotes) / totalvotes) * 100 : 0,
    supplemental: supplementalCount > 0,
    supplemental_count: supplementalCount,
    official: officialCount > 0,
    official_count: officialCount,
    county_count: countyCount,
    source_name: supplementalCount > 0 ? "Mixed MIT + supplemental county rows" : undefined,
    quality_grade: supplementalCount > 0 ? "D" : undefined,
  };
}

function provenanceItems(label: string, result: CountyResult | undefined) {
  if (!result) return [];
  const countyCount = result.county_count;
  const scope = (count: number) => (countyCount && countyCount > 1 ? `${formatNumber(count)} of ${formatNumber(countyCount)} counties` : "county row");
  const items: Array<{ kind: "official" | "supplemental"; text: string }> = [];

  if (result.official) {
    const officialCount = result.official_count ?? 1;
    items.push({
      kind: "official",
      text: `${label}: official state source ${scope(officialCount)}, grade A`,
    });
  }

  if (result.supplemental) {
    const supplementalCount = result.supplemental_count ?? 1;
    const quality = result.quality_grade ? `, grade ${result.quality_grade}` : "";
    items.push({
      kind: "supplemental",
      text: `${label}: supplemental ${scope(supplementalCount)}${quality}`,
    });
  }

  return items;
}

function optionValue(option: SelectOption) {
  return typeof option === "string" ? option : option.value;
}

function optionLabel(option: SelectOption) {
  return typeof option === "string" ? option : option.label;
}

function useElectionData() {
  const [data, setData] = useState<ElectionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/results/county-presidential-summary.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<ElectionSummary>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  return { data, error };
}

function useFloridaDistrictData() {
  const [data, setData] = useState<FloridaDistrictDrilldown | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/results/districts/florida-district-drilldown.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<FloridaDistrictDrilldown>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  return { data, error };
}

function useCaliforniaDistrictData() {
  const [data, setData] = useState<FloridaDistrictDrilldown | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/results/districts/california-district-drilldown.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<FloridaDistrictDrilldown>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  return { data, error };
}

function useFloridaStatewideData() {
  const [data, setData] = useState<FloridaStatewideSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/results/florida-statewide-summary.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<FloridaStatewideSummary>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  return { data, error };
}

function useFloridaPrecinctCatalog() {
  const [data, setData] = useState<FloridaPrecinctCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/results/florida-precinct-catalog.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<FloridaPrecinctCatalog>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  return { data, error };
}

function useFloridaPrecinctData(entry: FloridaPrecinctCatalogEntry | null) {
  const [data, setData] = useState<FloridaPrecinctBundle | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!entry) {
      setData(null);
      setError(null);
      return;
    }
    setData(null);
    setError(null);
    fetch(entry.bundle_url)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<FloridaPrecinctBundle>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [entry]);

  return { data, error };
}

function useCaliforniaStatewideData() {
  const [data, setData] = useState<FloridaStatewideSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/results/california-statewide-summary.json")
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<FloridaStatewideSummary>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, []);

  return { data, error };
}

function useDistrictGeometry(url: string | undefined) {
  const [data, setData] = useState<DistrictFeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!url) return;
    setData(null);
    setError(null);
    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<DistrictFeatureCollection>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [url]);

  return { data, error };
}

function usePrecinctGeometry(url: string | undefined) {
  const [data, setData] = useState<PrecinctFeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!url) return;
    setData(null);
    setError(null);
    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<PrecinctFeatureCollection>;
      })
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [url]);

  return { data, error };
}

function SelectControl({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
}) {
  const selectedLabel = optionLabel(options.find((option) => optionValue(option) === value) ?? value);
  return (
    <label className="select-control">
      <span>{label}</span>
      <div className="select-shell">
        <span className="select-value">{selectedLabel}</span>
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          {options.map((option) => (
            <option key={optionValue(option)} value={optionValue(option)}>
              {optionLabel(option)}
            </option>
          ))}
        </select>
        <ChevronDown size={16} aria-hidden="true" />
      </div>
    </label>
  );
}

function ViewToggle({
  view,
  officialState,
  onNational,
  onOfficialState,
}: {
  view: ViewMode;
  officialState: OfficialStatePo;
  onNational: () => void;
  onOfficialState: (statePo: OfficialStatePo) => void;
}) {
  return (
    <div className="view-toggle" aria-label="Map view">
      <button className={view === "national" ? "active" : ""} onClick={onNational} type="button">
        <MapIcon size={16} />
        National
      </button>
      <label className={view === "official" ? "state-switch active" : "state-switch"}>
        <MapPinned size={16} />
        <span>{officialStateOptions.find((state) => state.value === officialState)?.label ?? officialState}</span>
        <select value={officialState} onChange={(event) => onOfficialState(event.target.value as OfficialStatePo)}>
          {officialStateOptions.map((state) => (
            <option key={state.value} value={state.value}>
              {state.label}
            </option>
          ))}
        </select>
        <ChevronDown size={16} aria-hidden="true" />
      </label>
    </div>
  );
}

function MetricToggle({ metric, onChange }: { metric: Metric; onChange: (metric: Metric) => void }) {
  return (
    <div className="metric-toggle" aria-label="Map metric">
      <button className={metric === "winner" ? "active" : ""} onClick={() => onChange("winner")} type="button">
        <MapPinned size={16} />
        Winner
      </button>
      <button className={metric === "shift" ? "active" : ""} onClick={() => onChange("shift")} type="button">
        <GitCompareArrows size={16} />
        Shift
      </button>
    </div>
  );
}

function NationalBoard({ counties, year }: { counties: CountySummary[]; year: string }) {
  const totals = useMemo(() => {
    const parties = new Map<string, number>();
    let totalvotes = 0;

    for (const county of counties) {
      const result = county.results[year];
      if (!result) continue;
      totalvotes += result.totalvotes;
      for (const [party, votes] of Object.entries(result.parties)) {
        parties.set(party, (parties.get(party) ?? 0) + votes);
      }
    }

    return {
      totalvotes,
      parties: [...parties.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4),
    };
  }, [counties, year]);

  const topVotes = max(totals.parties, ([, votes]) => votes) ?? 1;

  return (
    <section className="national-board">
      <div>
        <p className="eyebrow">National popular vote</p>
        <strong>{formatNumber(totals.totalvotes)}</strong>
      </div>
      <div className="party-bars">
        {totals.parties.map(([party, votes]) => (
          <div className="party-row" key={party}>
            <span style={{ color: partyColor(party) }}>{partyLabels[party] ?? party}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(votes / topVotes) * 100}%`, background: partyColor(party) }} />
            </div>
            <b>{formatNumber(votes)}</b>
          </div>
        ))}
      </div>
    </section>
  );
}

function FloridaBoard({ layer }: { layer: FloridaDistrictLayer }) {
  const totals = useMemo(() => {
    const parties = new Map<string, number>();
    let totalVotes = 0;
    for (const contest of layer.contests) {
      totalVotes += contest.total_votes;
      for (const candidate of contest.candidates) {
        parties.set(candidate.party, (parties.get(candidate.party) ?? 0) + candidate.votes);
      }
    }
    return {
      totalVotes,
      parties: [...parties.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4),
    };
  }, [layer]);
  const topVotes = max(totals.parties, ([, votes]) => votes) ?? 1;

  return (
    <section className="national-board">
      <div>
        <p className="eyebrow">{layer.office}</p>
        <strong>{formatNumber(totals.totalVotes)}</strong>
      </div>
      <div className="party-bars">
        {totals.parties.map(([party, votes]) => (
          <div className="party-row" key={party}>
            <span style={{ color: partyColor(party) }}>{partyLabels[party] ?? party}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(votes / topVotes) * 100}%`, background: partyColor(party) }} />
            </div>
            <b>{formatNumber(votes)}</b>
          </div>
        ))}
      </div>
    </section>
  );
}

function FloridaContestBoard({ title, contests }: { title: string; contests: FloridaContest[] }) {
  const totals = useMemo(() => {
    const parties = new Map<string, number>();
    let totalVotes = 0;
    for (const contest of contests) {
      totalVotes += contest.total_votes;
      for (const candidate of contest.candidates) {
        parties.set(candidate.party, (parties.get(candidate.party) ?? 0) + candidate.votes);
      }
    }
    return {
      totalVotes,
      parties: [...parties.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4),
    };
  }, [contests]);
  const topVotes = max(totals.parties, ([, votes]) => votes) ?? 1;

  return (
    <section className="national-board">
      <div>
        <p className="eyebrow">{title}</p>
        <strong>{formatNumber(totals.totalVotes)}</strong>
      </div>
      <div className="party-bars">
        {totals.parties.map(([party, votes]) => (
          <div className="party-row" key={party}>
            <span style={{ color: partyColor(party) }}>{partyLabels[party] ?? party}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(votes / topVotes) * 100}%`, background: partyColor(party) }} />
            </div>
            <b>{formatNumber(votes)}</b>
          </div>
        ))}
      </div>
    </section>
  );
}

function StateTicker({
  counties,
  year,
  selectedState,
  onSelectState,
}: {
  counties: CountySummary[];
  year: string;
  selectedState: string | null;
  onSelectState: (statePo: string) => void;
}) {
  const states = useMemo(() => {
    const grouped = rollup(
      counties,
      (rows) => {
        const dem = sum(rows, (county) => county.results[year]?.parties.DEMOCRAT ?? 0);
        const rep = sum(rows, (county) => county.results[year]?.parties.REPUBLICAN ?? 0);
        const total = sum(rows, (county) => county.results[year]?.totalvotes ?? 0);
        return { dem, rep, total, margin: total ? ((dem - rep) / total) * 100 : 0 };
      },
      (county) => county.state_po,
    );

    return [...grouped.entries()]
      .filter(([, result]) => result.total > 0)
      .sort((a, b) => Math.abs(a[1].margin) - Math.abs(b[1].margin))
      .slice(0, 12);
  }, [counties, year]);

  return (
    <div className="ticker" aria-label="Closest states">
      {states.map(([state, result]) => (
        <button className={state === selectedState ? "active" : ""} key={state} type="button" onClick={() => onSelectState(state)}>
          <b>{state}</b>
          <i className={result.margin >= 0 ? "dem-text" : "rep-text"}>{result.margin >= 0 ? "D" : "R"} +{formatPct(result.margin)}</i>
        </button>
      ))}
    </div>
  );
}

function FloridaTicker({ layer }: { layer: FloridaDistrictLayer }) {
  const closest = useMemo(
    () =>
      [...layer.contests]
        .sort((a, b) => Math.abs(signedContestMargin(a)) - Math.abs(signedContestMargin(b)))
        .slice(0, 12),
    [layer],
  );

  return (
    <div className="ticker" aria-label="Closest Florida district contests">
      {closest.map((contest) => {
        const margin = signedContestMargin(contest);
        return (
          <span key={contest.contest_id}>
            <b>{contest.district_label.replace("District ", "D")}</b>
            <i className={margin >= 0 ? "dem-text" : "rep-text"}>{contestLeader(contest)}</i>
          </span>
        );
      })}
    </div>
  );
}

function FloridaContestTicker({ contests }: { contests: FloridaContest[] }) {
  const closest = useMemo(() => [...contests].sort((a, b) => Math.abs(signedContestMargin(a)) - Math.abs(signedContestMargin(b))).slice(0, 12), [contests]);

  return (
    <div className="ticker" aria-label="Closest Florida contests">
      {closest.map((contest) => {
        const margin = signedContestMargin(contest);
        return (
          <span key={contest.contest_id}>
            <b>{contest.district_label?.replace("District ", "D") ?? contest.office}</b>
            <i className={margin >= 0 ? "dem-text" : "rep-text"}>{contestLeader(contest)}</i>
          </span>
        );
      })}
    </div>
  );
}

function PresidentialDetails({
  title,
  eyebrow,
  result,
  compare,
  year,
  compareYear,
  emptyMessage,
}: {
  title: string;
  eyebrow: string;
  result: CountyResult | undefined;
  compare: CountyResult | undefined;
  year: string;
  compareYear: string;
  emptyMessage: string;
}) {
  if (!result) {
    return (
      <aside className="details-panel">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p className="muted">{emptyMessage}</p>
      </aside>
    );
  }

  const shift = compare ? resultMargin(result) - resultMargin(compare) : null;
  const comparisonParties = Array.from(new Set([...Object.keys(result?.parties ?? {}), ...Object.keys(compare?.parties ?? {})])).sort((a, b) => {
    const order = ["DEMOCRAT", "REPUBLICAN", "LIBERTARIAN", "GREEN", "OTHER"];
    return (order.indexOf(a) === -1 ? 99 : order.indexOf(a)) - (order.indexOf(b) === -1 ? 99 : order.indexOf(b));
  });
  const comparisonRows = [
    ...comparisonParties.map((party) => ({
      label: partyLabels[party] ?? party,
      party,
      current: result?.parties[party] ?? 0,
      compare: compare ? compare.parties[party] ?? 0 : null,
    })),
    {
      label: "Total",
      current: result?.totalvotes ?? 0,
      compare: compare?.totalvotes ?? null,
    },
  ];
  const provenanceRows = [...provenanceItems(year, result), ...provenanceItems(compareYear, compare)];

  return (
    <aside className="details-panel">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <div className="detail-stat">
        <span>{year}</span>
        <strong>{resultLeader(result)}</strong>
      </div>
      <div className="detail-stat">
        <span>Shift from {compareYear}</span>
        {shift === null ? (
          <strong>N/A</strong>
        ) : (
          <strong className={shift >= 0 ? "dem-text" : "rep-text"}>
            {shift >= 0 ? "D" : "R"} +{formatPct(shift)}
          </strong>
        )}
      </div>
      <ComparisonTable currentLabel={year} compareLabel={compareYear} rows={comparisonRows} />
      {provenanceRows.length ? (
        <div className="provenance-list" aria-label="Data provenance">
          {provenanceRows.map((item) => (
            <span className={item.kind} key={item.text}>
              {item.text}
            </span>
          ))}
        </div>
      ) : null}
    </aside>
  );
}

function CountyDetails({ county, year, compareYear }: { county: CountySummary | null; year: string; compareYear: string }) {
  return (
    <PresidentialDetails
      title={county?.county_name ?? "Select a county"}
      eyebrow={county?.state ?? "County details"}
      result={county?.results[year]}
      compare={county?.results[compareYear]}
      year={year}
      compareYear={compareYear}
      emptyMessage="Hover or click on the map to inspect results and election-to-election change."
    />
  );
}

function AggregateDetails({
  detail,
  counties,
  year,
  compareYear,
}: {
  detail: AggregateDetail;
  counties: CountySummary[];
  year: string;
  compareYear: string;
}) {
  const scopedCounties = detail.scope === "country" ? counties : counties.filter((county) => county.state_po === detail.statePo);
  return (
    <PresidentialDetails
      title={detail.name}
      eyebrow={detail.scope === "country" ? "Country details" : "State details"}
      result={aggregateCountyResults(scopedCounties, year)}
      compare={aggregateCountyResults(scopedCounties, compareYear)}
      year={year}
      compareYear={compareYear}
      emptyMessage="No aggregate data is available for this selection."
    />
  );
}

function DistrictDetails({
  contest,
  previousContest,
  compareYear,
}: {
  contest: FloridaDistrictContest | null;
  previousContest: FloridaDistrictContest | null;
  compareYear: number | null;
}) {
  if (!contest) {
    return (
      <aside className="details-panel">
        <p className="eyebrow">District details</p>
        <h2>Select a district</h2>
        <p className="muted">Hover or click a district, or use the district selector, to inspect county-level returns.</p>
      </aside>
    );
  }

  const shift = previousContest ? signedContestMargin(contest) - signedContestMargin(previousContest) : null;
  const currentPartyVotes = candidateVotesByParty(contest.candidates);
  const previousPartyVotes = candidateVotesByParty(previousContest?.candidates ?? []);
  const comparisonParties = Array.from(new Set([...currentPartyVotes.keys(), ...previousPartyVotes.keys()])).sort((a, b) => {
    const order = ["DEMOCRAT", "REPUBLICAN", "LIBERTARIAN", "GREEN", "NONPARTISAN", "OTHER"];
    return (order.indexOf(a) === -1 ? 99 : order.indexOf(a)) - (order.indexOf(b) === -1 ? 99 : order.indexOf(b));
  });
  const comparisonRows = previousContest
    ? [
        ...comparisonParties.map((party) => ({
          label: partyLabels[party] ?? party,
          party,
          current: currentPartyVotes.get(party) ?? 0,
          compare: previousPartyVotes.get(party) ?? 0,
        })),
        {
          label: "Total",
          current: contest.total_votes,
          compare: previousContest.total_votes,
        },
      ]
    : [];

  return (
    <aside className="details-panel">
      <p className="eyebrow">{contest.office}</p>
      <h2>{contest.district_label}</h2>
      <div className="detail-stat">
        <span>Total votes</span>
        <strong>{formatNumber(contest.total_votes)}</strong>
      </div>
      <div className="detail-stat">
        <span>Leader</span>
        <strong className={contest.winner.party === "REPUBLICAN" ? "rep-text" : "dem-text"}>{contestLeader(contest)}</strong>
      </div>
      {compareYear ? (
        <div className="detail-stat">
          <span>Shift from {compareYear}</span>
          {shift === null ? (
            <strong>No baseline</strong>
          ) : (
            <strong className={shift >= 0 ? "dem-text" : "rep-text"}>
              {shift >= 0 ? "D" : "R"} +{formatPct(shift)}
            </strong>
          )}
        </div>
      ) : null}
      {compareYear && previousContest ? <ComparisonTable currentLabel="Current" compareLabel={String(compareYear)} rows={comparisonRows} /> : null}
      {!previousContest ? (
        <div className="vote-list">
          {contest.candidates.map((candidate) => (
            <div key={`${candidate.candidate}-${candidate.party}`}>
              <span style={{ color: partyColor(candidate.party) }}>{candidate.candidate}</span>
              <b>{formatNumber(candidate.votes)}</b>
            </div>
          ))}
        </div>
      ) : null}
      <div className="county-breakdown">
        <p className="eyebrow">County split</p>
        {contest.counties.map((county) => (
          <div key={county.fips}>
            <span>{county.county_name}</span>
            <b>{contestLeader({ ...contest, winner: county.winner, margin_votes: county.margin_votes, total_votes: county.total_votes, candidates: county.candidates })}</b>
          </div>
        ))}
      </div>
    </aside>
  );
}

function floridaCountyToResult(county: FloridaContestCounty | undefined): CountyResult | undefined {
  if (!county) return undefined;
  const parties: Record<string, number> = {};
  for (const candidate of county.candidates) parties[candidate.party] = (parties[candidate.party] ?? 0) + candidate.votes;
  const ordered = Object.entries(parties).sort((a, b) => b[1] - a[1]);
  const [winnerParty, winnerVotes] = ordered[0] ?? ["OTHER", 0];
  const runnerUpVotes = ordered[1]?.[1] ?? 0;
  const demVotes = parties.DEMOCRAT ?? 0;
  const repVotes = parties.REPUBLICAN ?? 0;
  const marginVotes = winnerVotes - runnerUpVotes;
  return {
    totalvotes: county.total_votes,
    parties,
    winner_party: winnerParty,
    winner_votes: winnerVotes,
    margin_votes: marginVotes,
    margin_pct: county.total_votes ? (marginVotes / county.total_votes) * 100 : 0,
    dem_share: county.total_votes ? (demVotes / county.total_votes) * 100 : 0,
    rep_share: county.total_votes ? (repVotes / county.total_votes) * 100 : 0,
    two_party_margin: county.total_votes ? ((demVotes - repVotes) / county.total_votes) * 100 : 0,
    official: true,
    source_name: "Official state election source",
    quality_grade: "A",
  };
}

function aggregateFloridaCounty(counties: FloridaContestCounty[]): FloridaContestCounty | undefined {
  if (!counties.length) return undefined;
  const candidateVotes = new Map<string, CandidateResult>();
  let totalVotes = 0;
  for (const county of counties) {
    totalVotes += county.total_votes;
    for (const candidate of county.candidates) {
      const key = `${candidate.party}:${candidate.candidate}`;
      const current = candidateVotes.get(key);
      if (current) current.votes += candidate.votes;
      else candidateVotes.set(key, { ...candidate });
    }
  }
  const candidates = [...candidateVotes.values()].sort((a, b) => b.votes - a.votes);
  const winner = candidates[0] ?? { candidate: "Unknown", party: "OTHER", votes: 0 };
  const runnerUpVotes = candidates[1]?.votes ?? 0;
  return {
    fips: counties[0].fips,
    county_name: counties[0].county_name,
    total_votes: totalVotes,
    winner,
    margin_votes: winner.votes - runnerUpVotes,
    candidates,
  };
}

function FloridaCountyDetails({
  county,
  title,
  sourceLabel,
}: {
  county: FloridaContestCounty | null;
  title: string;
  sourceLabel: string;
}) {
  if (!county) {
    return (
      <aside className="details-panel">
        <p className="eyebrow">{title}</p>
        <h2>Select a county</h2>
        <p className="muted">Hover or click a county to inspect official county returns.</p>
      </aside>
    );
  }

  return (
    <aside className="details-panel">
      <p className="eyebrow">{title}</p>
      <h2>{county.county_name}</h2>
      <div className="detail-stat">
        <span>Total votes</span>
        <strong>{formatNumber(county.total_votes)}</strong>
      </div>
      <div className="detail-stat">
        <span>Leader</span>
        <strong className={county.winner.party === "REPUBLICAN" ? "rep-text" : "dem-text"}>
          {resultLeader(floridaCountyToResult(county))}
        </strong>
      </div>
      <div className="vote-list">
        {county.candidates.map((candidate) => (
          <div key={`${candidate.candidate}-${candidate.party}`}>
            <span style={{ color: partyColor(candidate.party) }}>{candidate.candidate}</span>
            <b>{formatNumber(candidate.votes)}</b>
          </div>
        ))}
      </div>
      <div className="provenance-list" aria-label="Data provenance">
        <span className="official">{sourceLabel}, grade A</span>
      </div>
    </aside>
  );
}

function countyContestColor(county: FloridaContestCounty | undefined) {
  return mapColor(floridaCountyToResult(county), undefined, "winner");
}

function FloridaCountyMapView({
  election,
  contests,
  title,
  statePo,
  sourceLabel,
}: {
  election: FloridaStatewideElection;
  contests: FloridaContest[];
  title: string;
  statePo: string;
  sourceLabel: string;
}) {
  const [selectedFips, setSelectedFips] = useState<string | null>(null);
  const [hoveredFips, setHoveredFips] = useState<string | null>(null);

  const countyFeatures = useMemo(() => {
    const topology = us as UsTopology;
    const collection = feature(topology, topology.objects.counties) as GeoJSON.FeatureCollection;
    const prefix = stateFipsPrefixes[statePo] ?? "";
    return (collection.features as CountyFeature[]).filter((county) => String(county.id ?? "").startsWith(prefix));
  }, [statePo]);
  const projection = useMemo(() => geoAlbersUsa().fitSize([975, 610], { type: "FeatureCollection", features: countyFeatures }), [countyFeatures]);
  const path = useMemo(() => geoPath(projection), [projection]);
  const countiesByFips = useMemo(() => {
    const map = new Map<string, FloridaContestCounty[]>();
    for (const contest of contests) {
      for (const county of contest.counties) {
        const rows = map.get(county.fips) ?? [];
        rows.push(county);
        map.set(county.fips, rows);
      }
    }
    return new Map([...map.entries()].map(([fips, rows]) => [fips, aggregateFloridaCounty(rows)]));
  }, [contests]);
  const activeCounty = countiesByFips.get(hoveredFips ?? selectedFips ?? "") ?? null;

  return (
    <section className="dashboard">
      <div className="map-stage florida-map">
        <svg viewBox="0 0 975 610" role="img" aria-label={`${election.election.state} ${election.election.year} ${title} county map`}>
          <g>
            {countyFeatures.map((county) => {
              const fips = String(county.id ?? "");
              const row = countiesByFips.get(fips);
              const active = fips === selectedFips || fips === hoveredFips;
              return (
                <path
                  key={fips}
                  d={path(county) ?? undefined}
                  fill={countyContestColor(row)}
                  className={active ? "map-unit active" : "map-unit"}
                  onMouseEnter={() => setHoveredFips(fips)}
                  onMouseLeave={() => setHoveredFips(null)}
                  onClick={() => setSelectedFips(row ? fips : null)}
                >
                  <title>{row ? `${row.county_name}: ${resultLeader(floridaCountyToResult(row))}` : "No data"}</title>
                </path>
              );
            })}
          </g>
        </svg>
        <MapLegend />
      </div>

      <div className="side-stack">
        <FloridaContestBoard title={title} contests={contests} />
        <FloridaCountyDetails county={activeCounty} title={title} sourceLabel={sourceLabel} />
        <SourcePanel sourceUrl={election.source.url}>{sourceLabel}</SourcePanel>
      </div>
    </section>
  );
}

function SourcePanel({ sourceUrl, children }: { sourceUrl: string; children: React.ReactNode }) {
  return (
    <section className="source-panel">
      <p className="eyebrow">Source</p>
      <a href={sourceUrl} target="_blank" rel="noreferrer">
        {children}
      </a>
    </section>
  );
}

function NationalMapView({
  data,
  year,
  compareYear,
  metric,
  aggregateDetail,
  onAggregateDetail,
}: {
  data: ElectionSummary;
  year: string;
  compareYear: string;
  metric: Metric;
  aggregateDetail: AggregateDetail | null;
  onAggregateDetail: (detail: AggregateDetail | null) => void;
}) {
  const [selectedFips, setSelectedFips] = useState<string | null>(null);
  const [hoveredFips, setHoveredFips] = useState<string | null>(null);

  useEffect(() => {
    if (aggregateDetail) {
      setSelectedFips(null);
      setHoveredFips(null);
    }
  }, [aggregateDetail]);

  const countyFeatures = useMemo(() => {
    const topology = us as UsTopology;
    const collection = feature(topology, topology.objects.counties) as GeoJSON.FeatureCollection;
    return collection.features as CountyFeature[];
  }, []);

  const stateMesh = useMemo(() => {
    const topology = us as UsTopology;
    return mesh(topology, topology.objects.states, (a, b) => a !== b);
  }, []);

  const projection = useMemo(() => geoAlbersUsa().fitSize([975, 610], { type: "Sphere" }), []);
  const path = useMemo(() => geoPath(projection), [projection]);

  const countiesByFips = useMemo(() => {
    const map = new Map<string, CountySummary>();
    for (const county of data.counties) map.set(county.fips, county);
    return map;
  }, [data]);

  const activeCounty = countiesByFips.get(hoveredFips ?? selectedFips ?? "") ?? null;
  const activeDetails =
    activeCounty || !aggregateDetail ? (
      <CountyDetails county={activeCounty} year={year} compareYear={compareYear} />
    ) : (
      <AggregateDetails detail={aggregateDetail} counties={data.counties} year={year} compareYear={compareYear} />
    );

  return (
    <section className="dashboard" onClick={() => onAggregateDetail({ scope: "country", name: "United States" })}>
      <div className="map-stage">
        <svg viewBox="0 0 975 610" role="img" aria-label={`County presidential election map for ${year}`}>
          <g>
            {countyFeatures.map((county) => {
              const fips = String(county.id ?? "");
              const row = countiesByFips.get(fips);
              const result = row?.results[year];
              const previous = row?.results[compareYear];
              const active = fips === selectedFips || fips === hoveredFips;
              return (
                <path
                  key={fips}
                  d={path(county) ?? undefined}
                  fill={mapColor(result, previous, metric)}
                  className={active ? "map-unit active" : "map-unit"}
                  onMouseEnter={() => setHoveredFips(fips)}
                  onMouseLeave={() => setHoveredFips(null)}
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelectedFips(fips);
                    onAggregateDetail(null);
                  }}
                  onDoubleClick={(event) => {
                    event.stopPropagation();
                    if (!row) return;
                    setSelectedFips(null);
                    setHoveredFips(null);
                    onAggregateDetail({ scope: "state", statePo: row.state_po, name: row.state });
                  }}
                >
                  <title>{row ? `${row.county_name}, ${row.state_po}: ${resultLeader(result)}` : "No data"}</title>
                </path>
              );
            })}
          </g>
          <path d={path(stateMesh) ?? undefined} className="state-lines" />
        </svg>
        <MapLegend />
      </div>

      <div className="side-stack" onClick={(event) => event.stopPropagation()}>
        <NationalBoard counties={data.counties} year={year} />
        {activeDetails}
        <SourcePanel sourceUrl={data.source.url}>
          {data.source.official_state_sources?.length || data.source.supplements?.length
            ? "MIT county presidential returns + official state rows + supplemental CSVs"
            : "MIT county presidential returns"}
        </SourcePanel>
      </div>
    </section>
  );
}

function FloridaDistrictMapView({
  election,
  layer,
  previousLayer,
  compareYear,
  metric,
  sourceLabel,
  selectedContestId,
  hoveredContestId,
  onSelectedContest,
  onHoveredContest,
}: {
  election: FloridaDistrictElection;
  layer: FloridaDistrictLayer;
  previousLayer: FloridaDistrictLayer | null;
  compareYear: number | null;
  metric: Metric;
  sourceLabel: string;
  selectedContestId: number | null;
  hoveredContestId: number | null;
  onSelectedContest: (contestId: number | null) => void;
  onHoveredContest: (contestId: number | null) => void;
}) {
  const { data: geometry, error } = useDistrictGeometry(layer.geometry_url);
  const contestsByGeometryId = useMemo(() => {
    const map = new Map<number, FloridaDistrictContest>();
    for (const contest of layer.contests) map.set(contest.geometry_id, contest);
    return map;
  }, [layer]);
  const previousContestsByGeometryId = useMemo(() => {
    const map = new Map<number, FloridaDistrictContest>();
    for (const contest of previousLayer?.contests ?? []) map.set(contest.geometry_id, contest);
    return map;
  }, [previousLayer]);
  const activeContest = layer.contests.find((contest) => contest.contest_id === (hoveredContestId ?? selectedContestId)) ?? null;
  const activePreviousContest = activeContest ? previousContestsByGeometryId.get(activeContest.geometry_id) ?? null : null;
  const projection = useMemo(() => (geometry ? geoAlbersUsa().fitSize([975, 610], geometry) : null), [geometry]);
  const path = useMemo(() => (projection ? geoPath(projection) : null), [projection]);

  return (
    <section className="dashboard">
      <div className="map-stage florida-map">
        {!geometry || !path ? (
          <div className="map-status">{error ? `Could not load district geometry: ${error}` : `Loading ${election.election.state} districts...`}</div>
        ) : (
          <svg viewBox="0 0 975 610" role="img" aria-label={`${election.election.state} ${election.election.year} ${layer.office} district map`}>
            <g>
              {(geometry.features as DistrictFeature[]).map((district) => {
                const geometryId = Number(district.properties?.geometry_id);
                const contest = contestsByGeometryId.get(geometryId);
                const previousContest = previousContestsByGeometryId.get(geometryId);
                const active = contest?.contest_id === selectedContestId || contest?.contest_id === hoveredContestId;
                return (
                  <path
                    key={district.id ?? geometryId}
                    d={path(district) ?? undefined}
                    fill={districtColor(contest, previousContest, metric)}
                    className={active ? "map-unit district active" : "map-unit district"}
                    onMouseEnter={() => onHoveredContest(contest?.contest_id ?? null)}
                    onMouseLeave={() => onHoveredContest(null)}
                    onClick={() => onSelectedContest(contest?.contest_id ?? null)}
                  >
                    <title>
                      {contest
                        ? `${contest.district_label}: ${
                            metric === "shift" && previousContest
                              ? `shift ${signedContestMargin(contest) - signedContestMargin(previousContest) >= 0 ? "D" : "R"} +${formatPct(
                                  signedContestMargin(contest) - signedContestMargin(previousContest),
                                )}`
                              : contestLeader(contest)
                          }`
                        : String(district.properties?.district_label ?? "No contest")}
                    </title>
                  </path>
                );
              })}
            </g>
          </svg>
        )}
        <MapLegend />
      </div>

      <div className="side-stack">
        <FloridaBoard layer={layer} />
        <DistrictDetails contest={activeContest} previousContest={activePreviousContest} compareYear={compareYear} />
        <SourcePanel sourceUrl={election.source.url}>{sourceLabel}</SourcePanel>
      </div>
    </section>
  );
}

function precinctColor(row: FloridaPrecinctRecord | undefined) {
  if (!row?.winner || row.total_votes === 0) return "#3f3f46";
  const marginPct = (row.margin_votes / row.total_votes) * 100;
  return row.winner.party === "REPUBLICAN" ? winnerScale(-marginPct) : row.winner.party === "DEMOCRAT" ? winnerScale(marginPct) : "#71717a";
}

function FloridaPrecinctDetails({ row, contest }: { row: FloridaPrecinctRecord | null; contest: FloridaPrecinctContest }) {
  if (!row) {
    return (
      <aside className="details-panel">
        <p className="eyebrow">Precinct detail</p>
        <h2>Select a precinct</h2>
        <p className="muted">Hover or click a precinct to inspect official candidate totals.</p>
      </aside>
    );
  }

  return (
    <aside className="details-panel">
      <p className="eyebrow">{contest.name}</p>
      <h2>Precinct {row.precinct_id}</h2>
      <div className="detail-stat">
        <span>Total votes</span>
        <strong>{formatNumber(row.total_votes)}</strong>
      </div>
      <div className="detail-stat">
        <span>Leader</span>
        <strong style={{ color: row.winner ? partyColor(row.winner.party) : undefined }}>
          {row.winner ? `${partyLabels[row.winner.party] ?? row.winner.party} +${formatNumber(row.margin_votes)}` : "No data"}
        </strong>
      </div>
      <div className="vote-list">
        {row.candidates.map((candidate) => (
          <div key={`${candidate.candidate}-${candidate.party}`}>
            <span style={{ color: partyColor(candidate.party) }}>{candidate.candidate}</span>
            <b>{formatNumber(candidate.votes)}</b>
          </div>
        ))}
      </div>
      <div className="provenance-list" aria-label="Data provenance">
        <span className="official">Florida Division of Elections, grade A</span>
      </div>
    </aside>
  );
}

function FloridaPrecinctMapView({ bundle, contest }: { bundle: FloridaPrecinctBundle; contest: FloridaPrecinctContest }) {
  const { data: geometry, error } = usePrecinctGeometry(bundle.geometry.geometry_url);
  const [selectedPrecinct, setSelectedPrecinct] = useState<string | null>(null);
  const [hoveredPrecinct, setHoveredPrecinct] = useState<string | null>(null);
  const rowsByPrecinct = useMemo(() => new Map(contest.precincts.map((row) => [row.precinct_id, row])), [contest]);
  const projection = useMemo(() => (geometry ? geoMercator().fitSize([975, 610], geometry) : null), [geometry]);
  const path = useMemo(() => (projection ? geoPath(projection) : null), [projection]);
  const activeRow = rowsByPrecinct.get(hoveredPrecinct ?? selectedPrecinct ?? "") ?? null;

  return (
    <section className="dashboard">
      <div className="map-stage florida-map">
        {!geometry || !path ? (
          <div className="map-status">{error ? `Could not load precinct geometry: ${error}` : `Loading ${bundle.county.name} precincts...`}</div>
        ) : (
          <svg viewBox="0 0 975 610" role="img" aria-label={`${bundle.election.year} ${bundle.county.name} ${contest.name} precinct map`}>
            <g>
              {(geometry.features as PrecinctFeature[]).map((precinct) => {
                const precinctId = String(precinct.properties?.precinct_id ?? "");
                const row = rowsByPrecinct.get(precinctId);
                const active = precinctId === selectedPrecinct || precinctId === hoveredPrecinct;
                return (
                  <path
                    key={precinct.id ?? precinctId}
                    d={path(precinct) ?? undefined}
                    fill={precinctColor(row)}
                    className={active ? "map-unit district active" : "map-unit district"}
                    onMouseEnter={() => setHoveredPrecinct(precinctId)}
                    onMouseLeave={() => setHoveredPrecinct(null)}
                    onClick={() => setSelectedPrecinct(row ? precinctId : null)}
                  >
                    <title>{row ? `Precinct ${precinctId}: ${row.winner?.candidate ?? "No data"}` : `Precinct ${precinctId}: No result join`}</title>
                  </path>
                );
              })}
            </g>
          </svg>
        )}
        <MapLegend />
      </div>
      <div className="side-stack">
        <section className="details-panel">
          <p className="eyebrow">Official precinct returns</p>
          <h2>{contest.name}</h2>
          <div className="detail-stat"><span>Result precincts</span><strong>{formatNumber(bundle.geometry.result_precinct_count ?? rowsByPrecinct.size)}</strong></div>
          <div className="detail-stat"><span>Matched to geometry</span><strong>{formatNumber(bundle.geometry.matched_result_precinct_count ?? rowsByPrecinct.size)}</strong></div>
          {(bundle.geometry.unmatched_result_precinct_count ?? 0) > 0 ? (
            <div className="detail-stat"><span>Unmatched result IDs</span><strong>{formatNumber(bundle.geometry.unmatched_result_precinct_count ?? 0)}</strong></div>
          ) : null}
          <div className="detail-stat"><span>Geometry vintage</span><strong>{bundle.geometry.vintage}</strong></div>
          <div className="detail-stat"><span>Geometry payload</span><strong>{formatBytes(bundle.geometry.file_size_bytes)}</strong></div>
          <a href="/results/florida-precinct-join-report.json" download>Download join audit</a>
        </section>
        <FloridaPrecinctDetails row={activeRow} contest={contest} />
        <SourcePanel sourceUrl={bundle.source.url}>Florida Division of Elections precinct returns</SourcePanel>
      </div>
    </section>
  );
}

function MapLegend() {
  return (
    <div className="legend">
      <span className="rep-text">R</span>
      <i />
      <span>Even</span>
      <span className="dem-text">D</span>
    </div>
  );
}

function candidateOption(contest: FloridaDistrictContest) {
  return {
    value: String(contest.contest_id),
    label: `${contest.district_label} ${contestLeader(contest)}`,
  };
}

function AppContent({ nationalData }: { nationalData: ElectionSummary }) {
  const { data: floridaData, error: floridaError } = useFloridaDistrictData();
  const { data: californiaDistrictData, error: californiaDistrictError } = useCaliforniaDistrictData();
  const { data: floridaStatewideData, error: floridaStatewideError } = useFloridaStatewideData();
  const { data: californiaData, error: californiaError } = useCaliforniaStatewideData();
  const [view, setView] = useState<ViewMode>("national");
  const [officialState, setOfficialState] = useState<OfficialStatePo>("FL");
  const [year, setYear] = useState("2024");
  const [compareYear, setCompareYear] = useState("2020");
  const [metric, setMetric] = useState<Metric>("winner");
  const [floridaMetric, setFloridaMetric] = useState<Metric>("winner");
  const [aggregateDetail, setAggregateDetail] = useState<AggregateDetail | null>({ scope: "country", name: "United States" });
  const [floridaYear, setFloridaYear] = useState("2024");
  const [floridaOffice, setFloridaOffice] = useState("U.S. House");
  const [floridaMapLevel, setFloridaMapLevel] = useState<"district" | "precinct">("district");
  const [selectedFloridaContestId, setSelectedFloridaContestId] = useState<number | null>(null);
  const [californiaYear, setCaliforniaYear] = useState("2024");
  const [californiaOffice, setCaliforniaOffice] = useState("President");
  const [selectedCaliforniaContestId, setSelectedCaliforniaContestId] = useState<number | null>(null);
  const [selectedContestId, setSelectedContestId] = useState<number | null>(null);
  const [hoveredContestId, setHoveredContestId] = useState<number | null>(null);
  const { data: floridaPrecinctCatalog, error: floridaPrecinctCatalogError } = useFloridaPrecinctCatalog();
  const [floridaPrecinctCountyFips, setFloridaPrecinctCountyFips] = useState<string | null>(null);
  const isFloridaOfficial = view === "official" && officialState === "FL";
  const isCaliforniaOfficial = view === "official" && officialState === "CA";

  useEffect(() => {
    const latest = String(nationalData.years[nationalData.years.length - 1]);
    const previous = String(nationalData.years[nationalData.years.length - 2] ?? nationalData.years[0]);
    setYear(latest);
    setCompareYear(previous);
  }, [nationalData]);

  useEffect(() => {
    if (year !== compareYear) return;
    const fallback = nationalData.years.map(String).reverse().find((option) => option !== year);
    if (fallback) setCompareYear(fallback);
  }, [compareYear, nationalData.years, year]);

  const floridaElection = useMemo(
    () => floridaData?.elections.find((election) => String(election.election.year) === floridaYear) ?? null,
    [floridaData, floridaYear],
  );
  const floridaStatewideElection = useMemo(
    () =>
      floridaStatewideData?.elections.find((election) => String(election.election.year) === floridaYear) ??
      floridaStatewideData?.elections.at(-1) ??
      null,
    [floridaStatewideData, floridaYear],
  );
  const floridaPrecinctOptions = useMemo(
    () => floridaPrecinctCatalog?.bundles.filter((entry) => String(entry.year) === floridaYear && entry.map_ready) ?? [],
    [floridaPrecinctCatalog, floridaYear],
  );
  const selectedFloridaPrecinctEntry = useMemo(
    () => floridaPrecinctOptions.find((entry) => entry.county_fips === floridaPrecinctCountyFips) ?? floridaPrecinctOptions[0] ?? null,
    [floridaPrecinctCountyFips, floridaPrecinctOptions],
  );
  const { data: floridaPrecinctData, error: floridaPrecinctError } = useFloridaPrecinctData(selectedFloridaPrecinctEntry);
  const floridaOfficeContests = useMemo(() => {
    if (!floridaStatewideElection) return [];
    return floridaStatewideElection.contests.filter((contest) => contest.office === floridaOffice);
  }, [floridaOffice, floridaStatewideElection]);
  const floridaPrecinctContests = useMemo(
    () => floridaPrecinctData?.contests.filter((contest) => contest.office === floridaOffice) ?? [],
    [floridaOffice, floridaPrecinctData],
  );
  const selectedFloridaPrecinctContest = useMemo(
    () => floridaPrecinctContests.find((contest) => contest.contest_id === selectedFloridaContestId) ?? floridaPrecinctContests[0] ?? null,
    [floridaPrecinctContests, selectedFloridaContestId],
  );
  const selectedFloridaContests = useMemo(() => {
    if (selectedFloridaContestId === null) return floridaOfficeContests;
    return floridaOfficeContests.filter((contest) => contest.contest_id === selectedFloridaContestId);
  }, [floridaOfficeContests, selectedFloridaContestId]);
  const californiaElection = useMemo(
    () =>
      californiaData?.elections.find((election) => String(election.election.year) === californiaYear) ??
      californiaData?.elections.at(-1) ??
      null,
    [californiaData, californiaYear],
  );
  const californiaDistrictElection = useMemo(
    () => californiaDistrictData?.elections.find((election) => String(election.election.year) === californiaYear) ?? null,
    [californiaDistrictData, californiaYear],
  );
  const californiaOfficeContests = useMemo(() => {
    if (!californiaElection) return [];
    return californiaElection.contests.filter((contest) => contest.office === californiaOffice);
  }, [californiaElection, californiaOffice]);
  const selectedCaliforniaContests = useMemo(() => {
    if (selectedCaliforniaContestId === null) return californiaOfficeContests;
    return californiaOfficeContests.filter((contest) => contest.contest_id === selectedCaliforniaContestId);
  }, [californiaOfficeContests, selectedCaliforniaContestId]);

  const floridaLayer = useMemo(() => {
    if (!floridaElection) return null;
    return floridaElection.layers.find((layer) => layer.office === floridaOffice) ?? null;
  }, [floridaElection, floridaOffice]);
  const californiaLayer = useMemo(() => {
    if (!californiaDistrictElection) return null;
    return californiaDistrictElection.layers.find((layer) => layer.office === californiaOffice) ?? null;
  }, [californiaDistrictElection, californiaOffice]);

  const previousCaliforniaDistrictElection = useMemo(() => {
    if (!californiaDistrictData || !californiaDistrictElection) return null;
    const currentYear = californiaDistrictElection.election.year;
    return (
      [...californiaDistrictData.elections]
        .filter((election) => election.election.year < currentYear)
        .sort((a, b) => b.election.year - a.election.year)[0] ?? null
    );
  }, [californiaDistrictData, californiaDistrictElection]);

  const previousCaliforniaLayer = useMemo(() => {
    if (!previousCaliforniaDistrictElection || !californiaLayer) return null;
    return previousCaliforniaDistrictElection.layers.find((layer) => layer.layer_key === californiaLayer.layer_key) ?? null;
  }, [californiaLayer, previousCaliforniaDistrictElection]);

  const previousFloridaElection = useMemo(() => {
    if (!floridaData || !floridaElection) return null;
    const currentYear = floridaElection.election.year;
    return (
      [...floridaData.elections]
        .filter((election) => election.election.year < currentYear)
        .sort((a, b) => b.election.year - a.election.year)[0] ?? null
    );
  }, [floridaData, floridaElection]);

  const previousFloridaLayer = useMemo(() => {
    if (!previousFloridaElection || !floridaLayer) return null;
    return previousFloridaElection.layers.find((layer) => layer.layer_key === floridaLayer.layer_key) ?? null;
  }, [floridaLayer, previousFloridaElection]);

  useEffect(() => {
    if (!floridaStatewideElection) return;
    if (!floridaStatewideElection.contests.some((contest) => contest.office === floridaOffice)) {
      setFloridaOffice(floridaStatewideElection.contests[0]?.office ?? "President");
    }
  }, [floridaOffice, floridaStatewideElection]);

  useEffect(() => {
    if (!californiaElection) return;
    if (!californiaElection.contests.some((contest) => contest.office === californiaOffice)) {
      setCaliforniaOffice(californiaElection.contests[0]?.office ?? "President");
    }
  }, [californiaElection, californiaOffice]);

  useEffect(() => {
    setSelectedContestId(null);
    setHoveredContestId(null);
    setSelectedFloridaContestId(null);
  }, [floridaYear, floridaOffice]);

  useEffect(() => {
    if (floridaPrecinctOptions.length && !floridaPrecinctOptions.some((entry) => entry.county_fips === floridaPrecinctCountyFips)) {
      setFloridaPrecinctCountyFips(floridaPrecinctOptions[0].county_fips);
    }
  }, [floridaPrecinctCountyFips, floridaPrecinctOptions]);

  useEffect(() => {
    setFloridaMapLevel(floridaYear === "2012" || floridaYear === "2014" ? "precinct" : "district");
  }, [floridaYear]);

  useEffect(() => {
    setSelectedCaliforniaContestId(null);
    setSelectedContestId(null);
    setHoveredContestId(null);
  }, [californiaYear, californiaOffice]);

  const nationalYearOptions = nationalData.years.map(String).reverse();
  const floridaYearOptions = (floridaStatewideData?.elections ?? []).map((election) => String(election.election.year)).sort((a, b) => Number(b) - Number(a));
  const floridaOfficeOptions = Array.from(new Set(floridaStatewideElection?.contests.map((contest) => contest.office) ?? ["President"]));
  const californiaYearOptions = (californiaData?.elections ?? []).map((election) => String(election.election.year)).sort((a, b) => Number(b) - Number(a));
  const californiaOfficeOptions = Array.from(new Set(californiaElection?.contests.map((contest) => contest.office) ?? ["President"]));
  const districtOptions: SelectOption[] = [
    { value: "all", label: "All districts" },
    ...(floridaLayer?.contests.map(candidateOption) ?? []),
  ];
  const californiaDistrictOptions: SelectOption[] = [
    { value: "all", label: "All districts" },
    ...(californiaLayer?.contests.map(candidateOption) ?? []),
  ];
  const floridaContestOptions: SelectOption[] = [
    { value: "all", label: floridaOfficeContests.length > 1 ? "All contests" : "Statewide" },
    ...floridaOfficeContests.map((contest) => ({
      value: String(contest.contest_id),
      label: `${contest.district_label ?? contest.office} ${contestLeader(contest)}`,
    })),
  ];
  const floridaPrecinctContestOptions: SelectOption[] = floridaPrecinctContests.map((contest) => ({
    value: String(contest.contest_id),
    label: contest.name,
  }));
  const californiaContestOptions: SelectOption[] = [
    { value: "all", label: californiaOfficeContests.length > 1 ? "All contests" : "Statewide" },
    ...californiaOfficeContests.map((contest) => ({
      value: String(contest.contest_id),
      label: `${contest.district_label ?? contest.office} ${contestLeader(contest)}`,
    })),
  ];
  const hasDistrictGeometry = Boolean(floridaMapLevel === "district" && floridaElection && floridaLayer && selectedFloridaContestId === null);
  const hasFloridaPrecinctData = Boolean(floridaPrecinctData);
  const hasCaliforniaDistrictGeometry = Boolean(californiaDistrictElection && californiaLayer && selectedCaliforniaContestId === null);
  const stateNamesByPo = useMemo(() => {
    const map = new Map<string, string>();
    for (const county of nationalData.counties) {
      if (!map.has(county.state_po)) map.set(county.state_po, county.state);
    }
    return map;
  }, [nationalData.counties]);
  const stateOptions: SelectOption[] = [
    { value: "country", label: "United States" },
    ...Array.from(stateNamesByPo.entries())
      .sort((a, b) => a[1].localeCompare(b[1]))
      .map(([statePo, name]) => ({ value: statePo, label: name })),
  ];
  const selectedStateValue = aggregateDetail?.scope === "state" ? aggregateDetail.statePo ?? "country" : "country";

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">Decision desk</p>
          <h1>{view === "national" ? "Election Night Map" : `${officialStateOptions.find((state) => state.value === officialState)?.label ?? officialState} Elections`}</h1>
        </div>
        <div className="controls">
          <ViewToggle
            view={view}
            officialState={officialState}
            onNational={() => setView("national")}
            onOfficialState={(statePo) => {
              setOfficialState(statePo);
              setView("official");
            }}
          />
          {view === "national" ? (
            <>
              <SelectControl label="Year" value={year} options={nationalYearOptions} onChange={setYear} />
              <SelectControl label="Compare" value={compareYear} options={nationalYearOptions.filter((option) => option !== year)} onChange={setCompareYear} />
              <SelectControl
                label="State"
                value={selectedStateValue}
                options={stateOptions}
                onChange={(value) =>
                  setAggregateDetail(
                    value === "country"
                      ? { scope: "country", name: "United States" }
                      : { scope: "state", statePo: value, name: stateNamesByPo.get(value) ?? value },
                  )
                }
              />
              <MetricToggle metric={metric} onChange={setMetric} />
            </>
          ) : officialState === "FL" ? (
            <>
              <SelectControl label="Year" value={floridaYear} options={floridaYearOptions} onChange={setFloridaYear} />
              <SelectControl label="Office" value={floridaOffice} options={floridaOfficeOptions} onChange={setFloridaOffice} />
              {floridaPrecinctOptions.length ? (
                <SelectControl
                  label="County"
                  value={selectedFloridaPrecinctEntry?.county_fips ?? ""}
                  options={floridaPrecinctOptions.map((entry) => ({ value: entry.county_fips, label: entry.county_name }))}
                  onChange={setFloridaPrecinctCountyFips}
                />
              ) : null}
              {floridaPrecinctOptions.length && floridaLayer ? (
                <SelectControl
                  label="Map"
                  value={floridaMapLevel}
                  options={[{ value: "district", label: "Districts" }, { value: "precinct", label: floridaPrecinctData?.county.name ?? "Precincts" }]}
                  onChange={(value) => setFloridaMapLevel(value as "district" | "precinct")}
                />
              ) : null}
              {hasDistrictGeometry ? (
                <SelectControl
                  label="District"
                  value={selectedContestId === null ? "all" : String(selectedContestId)}
                  options={districtOptions}
                  onChange={(value) => setSelectedContestId(value === "all" ? null : Number(value))}
                />
              ) : hasFloridaPrecinctData ? (
                <SelectControl
                  label="Contest"
                  value={selectedFloridaPrecinctContest ? String(selectedFloridaPrecinctContest.contest_id) : ""}
                  options={floridaPrecinctContestOptions}
                  onChange={(value) => setSelectedFloridaContestId(Number(value))}
                />
              ) : (
                <SelectControl
                  label="Contest"
                  value={selectedFloridaContestId === null ? "all" : String(selectedFloridaContestId)}
                  options={floridaContestOptions}
                  onChange={(value) => setSelectedFloridaContestId(value === "all" ? null : Number(value))}
                />
              )}
              {hasDistrictGeometry || hasFloridaPrecinctData ? <MetricToggle metric={floridaMetric} onChange={setFloridaMetric} /> : null}
            </>
          ) : (
            <>
              <SelectControl label="Year" value={californiaYear} options={californiaYearOptions} onChange={setCaliforniaYear} />
              <SelectControl label="Office" value={californiaOffice} options={californiaOfficeOptions} onChange={setCaliforniaOffice} />
              {hasCaliforniaDistrictGeometry ? (
                <SelectControl
                  label="District"
                  value={selectedContestId === null ? "all" : String(selectedContestId)}
                  options={californiaDistrictOptions}
                  onChange={(value) => setSelectedContestId(value === "all" ? null : Number(value))}
                />
              ) : (
                <SelectControl
                  label="Contest"
                  value={selectedCaliforniaContestId === null ? "all" : String(selectedCaliforniaContestId)}
                  options={californiaContestOptions}
                  onChange={(value) => setSelectedCaliforniaContestId(value === "all" ? null : Number(value))}
                />
              )}
              {hasCaliforniaDistrictGeometry ? <MetricToggle metric={floridaMetric} onChange={setFloridaMetric} /> : null}
            </>
          )}
        </div>
      </header>

      {view === "national" ? (
        <StateTicker
          counties={nationalData.counties}
          year={year}
          selectedState={aggregateDetail?.scope === "state" ? aggregateDetail.statePo ?? null : null}
          onSelectState={(statePo) => setAggregateDetail({ scope: "state", statePo, name: stateNamesByPo.get(statePo) ?? statePo })}
        />
      ) : isFloridaOfficial && hasDistrictGeometry && floridaLayer ? (
        <FloridaTicker layer={floridaLayer} />
      ) : isFloridaOfficial && selectedFloridaContests.length ? (
        <FloridaContestTicker contests={selectedFloridaContests} />
      ) : isCaliforniaOfficial && hasCaliforniaDistrictGeometry && californiaLayer ? (
        <FloridaTicker layer={californiaLayer} />
      ) : isCaliforniaOfficial && selectedCaliforniaContests.length ? (
        <FloridaContestTicker contests={selectedCaliforniaContests} />
      ) : null}

      {view === "national" ? (
        <NationalMapView
          data={nationalData}
          year={year}
          compareYear={compareYear}
          metric={metric}
          aggregateDetail={aggregateDetail}
          onAggregateDetail={setAggregateDetail}
        />
      ) : isFloridaOfficial && (floridaError || floridaStatewideError || floridaPrecinctCatalogError || floridaPrecinctError) ? (
        <section className="center-message inline-error">Could not load Florida data: {floridaError ?? floridaStatewideError ?? floridaPrecinctCatalogError ?? floridaPrecinctError}</section>
      ) : isFloridaOfficial && hasDistrictGeometry && floridaElection && floridaLayer ? (
        <FloridaDistrictMapView
          election={floridaElection}
          layer={floridaLayer}
          previousLayer={previousFloridaLayer}
          compareYear={previousFloridaElection?.election.year ?? null}
          metric={floridaMetric}
          sourceLabel={officialSourceLabels.FL}
          selectedContestId={selectedContestId}
          hoveredContestId={hoveredContestId}
          onSelectedContest={setSelectedContestId}
          onHoveredContest={setHoveredContestId}
        />
      ) : isFloridaOfficial && floridaPrecinctData && selectedFloridaPrecinctContest ? (
        <FloridaPrecinctMapView bundle={floridaPrecinctData} contest={selectedFloridaPrecinctContest} />
      ) : isFloridaOfficial && floridaStatewideElection && selectedFloridaContests.length ? (
        <FloridaCountyMapView
          election={floridaStatewideElection}
          contests={selectedFloridaContests}
          title={`${floridaStatewideElection.election.year} ${floridaOffice}`}
          statePo="FL"
          sourceLabel={officialSourceLabels.FL}
        />
      ) : isCaliforniaOfficial && (californiaError || californiaDistrictError) ? (
        <section className="center-message inline-error">Could not load California data: {californiaError ?? californiaDistrictError}</section>
      ) : isCaliforniaOfficial && hasCaliforniaDistrictGeometry && californiaDistrictElection && californiaLayer ? (
        <FloridaDistrictMapView
          election={californiaDistrictElection}
          layer={californiaLayer}
          previousLayer={previousCaliforniaLayer}
          compareYear={previousCaliforniaDistrictElection?.election.year ?? null}
          metric={floridaMetric}
          sourceLabel={officialSourceLabels.CA}
          selectedContestId={selectedContestId}
          hoveredContestId={hoveredContestId}
          onSelectedContest={setSelectedContestId}
          onHoveredContest={setHoveredContestId}
        />
      ) : isCaliforniaOfficial && californiaElection && selectedCaliforniaContests.length ? (
        <FloridaCountyMapView
          election={californiaElection}
          contests={selectedCaliforniaContests}
          title={`${californiaElection.election.year} ${californiaOffice}`}
          statePo="CA"
          sourceLabel={officialSourceLabels.CA}
        />
      ) : (
        <section className="center-message inline-error">Loading {officialStateOptions.find((state) => state.value === officialState)?.label ?? officialState} returns...</section>
      )}
    </main>
  );
}

export default function App() {
  const { data, error } = useElectionData();

  if (error) {
    return (
      <main className="app-shell center-message">
        <h1>Election Night Map</h1>
        <p>Could not load results: {error}</p>
        <code>npm run data:fetch</code>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="app-shell center-message">
        <RadioTower size={28} />
        <p>Loading election returns...</p>
      </main>
    );
  }

  return <AppContent nationalData={data} />;
}
