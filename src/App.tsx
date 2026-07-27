import { useEffect, useMemo, useState } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import { max, rollup, sum } from "d3-array";
import { scaleThreshold } from "d3-scale";
import { feature, mesh } from "topojson-client";
import { ChevronDown, GitCompareArrows, MapPinned, RadioTower } from "lucide-react";
import type { GeometryCollection, Topology } from "topojson-specification";
import us from "us-atlas/counties-10m.json";
import type { ElectionSummary, CountyResult, CountySummary } from "./types";

type Metric = "winner" | "shift";
type CountyFeature = GeoJSON.Feature<GeoJSON.Geometry, GeoJSON.GeoJsonProperties> & { id?: string | number };
type UsTopology = Topology<{
  counties: GeometryCollection;
  states: GeometryCollection;
}>;

const partyLabels: Record<string, string> = {
  DEMOCRAT: "Dem",
  REPUBLICAN: "Rep",
  LIBERTARIAN: "Lib",
  GREEN: "Grn",
  OTHER: "Other",
};

const winnerScale = scaleThreshold<number, string>()
  .domain([-60, -40, -20, -10, 0, 10, 20, 40, 60])
  .range(["#7f1d1d", "#b91c1c", "#ef4444", "#fca5a5", "#e5e7eb", "#93c5fd", "#3b82f6", "#1d4ed8", "#1e3a8a", "#172554"]);

const shiftScale = scaleThreshold<number, string>()
  .domain([-30, -15, -7.5, -2.5, 2.5, 7.5, 15, 30])
  .range(["#7f1d1d", "#b91c1c", "#ef4444", "#fecaca", "#e5e7eb", "#bfdbfe", "#60a5fa", "#2563eb", "#1e3a8a"]);

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

function formatPct(value: number) {
  return `${Math.abs(value).toFixed(1)}%`;
}

function partyColor(party: string) {
  if (party === "DEMOCRAT") return "#2563eb";
  if (party === "REPUBLICAN") return "#dc2626";
  if (party === "LIBERTARIAN") return "#ca8a04";
  if (party === "GREEN") return "#16a34a";
  return "#6b7280";
}

function resultMargin(result: CountyResult | undefined) {
  if (!result) return 0;
  return result.two_party_margin;
}

function mapColor(result: CountyResult | undefined, previous: CountyResult | undefined, metric: Metric) {
  if (!result) return "#d4d4d8";
  if (metric === "shift") {
    return shiftScale(resultMargin(result) - resultMargin(previous));
  }
  return winnerScale(resultMargin(result));
}

function resultLeader(result: CountyResult | undefined) {
  if (!result) return "No data";
  const leader = partyLabels[result.winner_party] ?? result.winner_party;
  return `${leader} +${formatPct(result.margin_pct)}`;
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

function SelectControl({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="select-control">
      <span>{label}</span>
      <div className="select-shell">
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <ChevronDown size={16} aria-hidden="true" />
      </div>
    </label>
  );
}

function MetricToggle({
  metric,
  onChange,
}: {
  metric: Metric;
  onChange: (metric: Metric) => void;
}) {
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

function StateTicker({ counties, year }: { counties: CountySummary[]; year: string }) {
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
        <span key={state}>
          <b>{state}</b>
          <i className={result.margin >= 0 ? "dem-text" : "rep-text"}>{result.margin >= 0 ? "D" : "R"} +{formatPct(result.margin)}</i>
        </span>
      ))}
    </div>
  );
}

function CountyDetails({
  county,
  year,
  compareYear,
}: {
  county: CountySummary | null;
  year: string;
  compareYear: string;
}) {
  if (!county) {
    return (
      <aside className="details-panel">
        <p className="eyebrow">County details</p>
        <h2>Select a county</h2>
        <p className="muted">Hover or click on the map to inspect results and election-to-election change.</p>
      </aside>
    );
  }

  const result = county.results[year];
  const compare = county.results[compareYear];
  const shift = resultMargin(result) - resultMargin(compare);
  const parties = Object.entries(result?.parties ?? {}).sort((a, b) => b[1] - a[1]);

  return (
    <aside className="details-panel">
      <p className="eyebrow">{county.state}</p>
      <h2>{county.county_name}</h2>
      <div className="detail-stat">
        <span>{year}</span>
        <strong>{resultLeader(result)}</strong>
      </div>
      <div className="detail-stat">
        <span>Shift from {compareYear}</span>
        <strong className={shift >= 0 ? "dem-text" : "rep-text"}>
          {shift >= 0 ? "D" : "R"} +{formatPct(shift)}
        </strong>
      </div>
      <div className="vote-list">
        {parties.map(([party, votes]) => (
          <div key={party}>
            <span style={{ color: partyColor(party) }}>{partyLabels[party] ?? party}</span>
            <b>{formatNumber(votes)}</b>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default function App() {
  const { data, error } = useElectionData();
  const [year, setYear] = useState("2024");
  const [compareYear, setCompareYear] = useState("2020");
  const [metric, setMetric] = useState<Metric>("winner");
  const [selectedFips, setSelectedFips] = useState<string | null>(null);
  const [hoveredFips, setHoveredFips] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;
    const latest = String(data.years[data.years.length - 1]);
    const previous = String(data.years[data.years.length - 2] ?? data.years[0]);
    setYear(latest);
    setCompareYear(previous);
  }, [data]);

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
    for (const county of data?.counties ?? []) map.set(county.fips, county);
    return map;
  }, [data]);

  const activeCounty = countiesByFips.get(hoveredFips ?? selectedFips ?? "") ?? null;
  const yearOptions = (data?.years ?? [2000, 2004, 2008, 2012, 2016, 2020, 2024]).map(String).reverse();

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

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">Decision desk</p>
          <h1>Election Night Map</h1>
        </div>
        <div className="controls">
          <SelectControl label="Year" value={year} options={yearOptions} onChange={setYear} />
          <SelectControl label="Compare" value={compareYear} options={yearOptions.filter((option) => option !== year)} onChange={setCompareYear} />
          <MetricToggle metric={metric} onChange={setMetric} />
        </div>
      </header>

      <StateTicker counties={data.counties} year={year} />

      <section className="dashboard">
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
                    className={active ? "county active" : "county"}
                    onMouseEnter={() => setHoveredFips(fips)}
                    onMouseLeave={() => setHoveredFips(null)}
                    onClick={() => setSelectedFips(fips)}
                  >
                    <title>{row ? `${row.county_name}, ${row.state_po}: ${resultLeader(result)}` : "No data"}</title>
                  </path>
                );
              })}
            </g>
            <path d={path(stateMesh) ?? undefined} className="state-lines" />
          </svg>
          <div className="legend">
            <span className="rep-text">R</span>
            <i />
            <span>Even</span>
            <i />
            <span className="dem-text">D</span>
          </div>
        </div>

        <div className="side-stack">
          <NationalBoard counties={data.counties} year={year} />
          <CountyDetails county={activeCounty} year={year} compareYear={compareYear} />
          <section className="source-panel">
            <p className="eyebrow">Source</p>
            <a href={data.source.url} target="_blank" rel="noreferrer">
              MIT county presidential returns
            </a>
            <span>Version {data.source.dataverse_version}</span>
          </section>
        </div>
      </section>
    </main>
  );
}
