import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, type LabResultRow, type LabsResponse } from "../api";
import { usePageTitle, useSyncVersion } from "../context/AppContext";
import { ChevronDownIcon, SparkleIcon, TrendDownIcon, TrendFlatIcon, TrendUpIcon } from "../icons";

function TrendCell({ r }: { r: LabResultRow }) {
  if (r.trend_direction === null || r.pct_change === null) {
    return <span className="trend-icon">—</span>;
  }
  const Icon = r.trend_direction === "up" ? TrendUpIcon : r.trend_direction === "down" ? TrendDownIcon : TrendFlatIcon;
  return (
    <span className="trend-icon">
      <Icon />
      {r.trend_direction === "flat" ? "steady" : `${r.pct_change > 0 ? "+" : ""}${r.pct_change}%`}
    </span>
  );
}

export function Labs() {
  usePageTitle("Lab Results");
  const syncVersion = useSyncVersion();
  const [data, setData] = useState<LabsResponse | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    Promise.all([api.labs(), api.summary()])
      .then(([labs, summaryRes]) => {
        setData(labs);
        setSummary(summaryRes.summary);
      })
      .catch(() => setData({ categories: [] }))
      .finally(() => setLoading(false));
  }, [syncVersion]);

  function toggle(category: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }

  return (
    <>
      {summary && (
        <div className="summary-card">
          <span className="summary-badge">
            <SparkleIcon size={12} />
            AI Summary
          </span>
          <div className="summary-text">
            <Markdown remarkPlugins={[remarkGfm]}>{summary}</Markdown>
          </div>
        </div>
      )}

      {loading && <div className="empty-state">Loading…</div>}

      {!loading && data?.categories.length === 0 && (
        <div className="empty-state">No lab results yet — click "Sync now" in the sidebar to pull your data from MyChart.</div>
      )}

      {data?.categories.map((cat) => {
        const isOpen = expanded.has(cat.category);
        return (
          <div className="section" key={cat.category}>
            <button
              className="section-header"
              onClick={() => toggle(cat.category)}
              style={{ width: "100%", border: "none", background: "none", cursor: "pointer", textAlign: "left" }}
            >
              <span className="section-title">
                {cat.category}
                <span className="section-count">{cat.results.length} tests</span>
              </span>
              <span className="section-chevron" style={{ transform: isOpen ? "none" : "rotate(-90deg)", display: "inline-flex" }}>
                <ChevronDownIcon />
              </span>
            </button>
            {isOpen && (
              <table className="lab-table">
                <thead>
                  <tr>
                    <th>Test</th>
                    <th>Result</th>
                    <th>Reference Range</th>
                    <th>Trend</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {cat.results.map((r) => (
                    <tr key={r.id}>
                      <td>
                        {r.display_name}
                        {r.out_of_range && <span className="badge-flag">{r.value! > (r.reference_range_high ?? Infinity) ? "High" : "Low"}</span>}
                      </td>
                      <td className="mono">
                        {r.value !== null ? r.value : r.value_text ?? "—"} {r.unit ?? ""}
                      </td>
                      <td className="mono">
                        {r.reference_range_text ??
                          (r.reference_range_low !== null || r.reference_range_high !== null
                            ? `${r.reference_range_low ?? ""}–${r.reference_range_high ?? ""}`
                            : "—")}
                      </td>
                      <td>
                        <TrendCell r={r} />
                      </td>
                      <td className="mono">{r.collected_at ? new Date(r.collected_at).toLocaleDateString() : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        );
      })}
    </>
  );
}
