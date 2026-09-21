import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AppShell } from "../components/AppShell";
import { api, type TrendMetric, type TrendResponse } from "../api";

export function Trends() {
  const [metrics, setMetrics] = useState<TrendMetric[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [trend, setTrend] = useState<TrendResponse | null>(null);

  function loadMetrics() {
    api.trendMetrics().then((m) => {
      setMetrics(m);
      if (m.length > 0 && !selected) setSelected(m[0].loinc_code);
    });
  }

  useEffect(loadMetrics, []);

  useEffect(() => {
    if (selected) api.trend(selected).then(setTrend);
  }, [selected]);

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
    <AppShell title="Trends" onSynced={loadMetrics}>
      <div className="content-scroll">
        {metrics.length === 0 && (
          <div className="empty-state">No trend data yet — sync your account, and trends will appear once you have lab history.</div>
        )}

        {metrics.length > 0 && (
          <div className="chip-row" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {metrics.map((m) => (
              <button
                key={m.loinc_code ?? m.display_name}
                className={`filter-pill ${selected === m.loinc_code ? "active" : ""}`}
                onClick={() => setSelected(m.loinc_code)}
              >
                {m.display_name} ({m.data_points})
              </button>
            ))}
          </div>
        )}

        {trend && chartData.length > 0 && (
          <div className="card">
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>
              {trend.display_name} {trend.unit ? `(${trend.unit})` : ""}
            </div>
            <ResponsiveContainer width="100%" height={320}>
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
      </div>
    </AppShell>
  );
}
