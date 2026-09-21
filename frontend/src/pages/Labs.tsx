import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AppShell } from "../components/AppShell";
import { api, type LabsResponse } from "../api";
import { SparkleIcon } from "../icons";

export function Labs() {
  const [data, setData] = useState<LabsResponse | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    Promise.all([api.labs(), api.summary()])
      .then(([labs, summaryRes]) => {
        setData(labs);
        setSummary(summaryRes.summary);
      })
      .catch(() => setData({ categories: [] }))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  return (
    <AppShell title="Lab Results" onSynced={load}>
      <div className="content-scroll">
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

        {data?.categories.map((cat) => (
          <div className="section" key={cat.category}>
            <div className="section-header">
              <span className="section-title">
                {cat.category}
                <span className="section-count">{cat.results.length} results</span>
              </span>
            </div>
            <table className="lab-table">
              <thead>
                <tr>
                  <th>Test</th>
                  <th>Result</th>
                  <th>Reference Range</th>
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
                    <td className="mono">{r.collected_at ? new Date(r.collected_at).toLocaleDateString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
