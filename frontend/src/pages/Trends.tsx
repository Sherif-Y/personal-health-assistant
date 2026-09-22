import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, type TrendMetric, type TrendResponse } from "../api";
import { usePageTitle, useSyncVersion } from "../context/AppContext";
import { ChevronDownIcon, SearchIcon } from "../icons";

export function Trends() {
  usePageTitle("Trends");
  const syncVersion = useSyncVersion();
  const [metrics, setMetrics] = useState<TrendMetric[]>([]);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<string | null>(null);
  const [trend, setTrend] = useState<TrendResponse | null>(null);

  useEffect(() => {
    api.trendMetrics().then((m) => {
      setMetrics(m);
      setSelected((prev) => {
        if (prev) return prev;
        // Default to the metric with the most history, so something useful shows immediately
        // instead of landing on a single-point (or non-numeric) test with nothing to plot.
        const withCode = m.filter((x) => x.loinc_code);
        if (withCode.length === 0) return prev;
        const best = withCode.reduce((a, b) => (b.data_points > a.data_points ? b : a));
        return best.loinc_code;
      });
    });
  }, [syncVersion]);

  useEffect(() => {
    if (selected) api.trend(selected).then(setTrend);
  }, [selected]);

  const filtered = useMemo(
    () => metrics.filter((m) => m.display_name.toLowerCase().includes(search.toLowerCase())),
    [metrics, search]
  );

  const byCategory = useMemo(() => {
    const grouped = new Map<string, TrendMetric[]>();
    for (const m of filtered) {
      if (!grouped.has(m.category)) grouped.set(m.category, []);
      grouped.get(m.category)!.push(m);
    }
    return grouped;
  }, [filtered]);

  function toggle(category: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }

  const chartData =
    trend?.points
      .filter((p) => p.value !== null)
      .map((p) => ({
        date: p.collected_at ? new Date(p.collected_at).toLocaleDateString() : "",
        value: p.value,
        low: p.reference_range_low,
        high: p.reference_range_high,
      })) ?? [];

  return (
    <>
      {metrics.length === 0 && (
        <div className="empty-state">No trend data yet — sync your account, and trends will appear once you have lab history.</div>
      )}

      {trend && chartData.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>
            {trend.display_name} {trend.unit ? `(${trend.unit})` : ""}
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: "var(--ink-faint)" }} />
              <YAxis tick={{ fontSize: 12, fill: "var(--ink-faint)" }} domain={["auto", "auto"]} />
              <Tooltip />
              {chartData[0]?.high != null && <ReferenceLine y={chartData[0].high!} stroke="#b54b1c" strokeDasharray="5 5" label="Upper limit" />}
              {chartData[0]?.low != null && <ReferenceLine y={chartData[0].low!} stroke="#b54b1c" strokeDasharray="5 5" label="Lower limit" />}
              <Line type="monotone" dataKey="value" stroke="#1f6f64" strokeWidth={2.5} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {trend && chartData.length === 1 && (
        <div className="empty-state">Only one data point so far for this test — trends will show once more results come in over time.</div>
      )}

      {trend && chartData.length === 0 && (
        <div className="empty-state">"{trend.display_name}" doesn't have plottable numeric history (its results may be text-based rather than numbers).</div>
      )}

      {metrics.length > 0 && (
        <div className="search-wrap" style={{ maxWidth: 320 }}>
          <span className="search-icon">
            <SearchIcon />
          </span>
          <label htmlFor="trend-search" style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>
            Search tests
          </label>
          <input
            id="trend-search"
            className="input-search"
            style={{ width: "100%" }}
            placeholder="Search a test to see its trend…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {Array.from(byCategory.entries()).map(([category, categoryMetrics]) => {
        const isOpen = expanded.has(category) || search.length > 0;
        return (
          <div className="section" key={category}>
            <button
              className="section-header"
              onClick={() => toggle(category)}
              style={{ width: "100%", border: "none", background: "none", cursor: "pointer", textAlign: "left" }}
            >
              <span className="section-title">
                {category}
                <span className="section-count">{categoryMetrics.length} tests</span>
              </span>
              <span className="section-chevron" style={{ transform: isOpen ? "none" : "rotate(-90deg)", display: "inline-flex" }}>
                <ChevronDownIcon />
              </span>
            </button>
            {isOpen && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", padding: "0 20px 16px" }}>
                {categoryMetrics.map((m) => (
                  <button
                    key={m.loinc_code ?? m.display_name}
                    className={`filter-pill ${selected === m.loinc_code ? "active" : ""}`}
                    onClick={() => setSelected(m.loinc_code)}
                    disabled={m.data_points < 2}
                    title={m.data_points < 2 ? "Only one data point so far" : undefined}
                    style={m.data_points < 2 ? { opacity: 0.5 } : undefined}
                  >
                    {m.display_name} ({m.data_points})
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}
