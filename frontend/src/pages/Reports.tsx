import { useEffect, useState } from "react";
import { AppShell } from "../components/AppShell";
import { api, type ReportRow } from "../api";
import { DocIcon } from "../icons";

export function Reports() {
  const [reports, setReports] = useState<ReportRow[]>([]);
  const [filter, setFilter] = useState<string | null>(null);

  function load() {
    api.reports(filter ?? undefined).then(setReports);
  }

  useEffect(load, [filter]);

  const types = Array.from(new Set(reports.map((r) => r.report_type).filter(Boolean))) as string[];

  return (
    <AppShell title="Reports" onSynced={load}>
      <div className="content-scroll">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className={`filter-pill ${!filter ? "active" : ""}`} onClick={() => setFilter(null)}>
            All
          </button>
          {types.map((t) => (
            <button key={t} className={`filter-pill ${filter === t ? "active" : ""}`} onClick={() => setFilter(t)}>
              {t}
            </button>
          ))}
        </div>

        {reports.length === 0 && <div className="empty-state">No reports found.</div>}

        {reports.map((r) => (
          <div className="card report-card" key={r.id}>
            <div className="report-top">
              <span className="report-badge">{r.report_type ?? r.resource_type}</span>
              <span className="report-title">{r.title}</span>
            </div>
            <div className="report-meta">{r.collected_at ? new Date(r.collected_at).toLocaleString() : "Date unknown"}</div>
            {r.narrative_text ? (
              <p className="report-summary">{r.narrative_text}</p>
            ) : (
              <p className="report-summary" style={{ color: "var(--ink-faint)", fontStyle: "italic" }}>
                Full report text isn't available yet for this item.
              </p>
            )}
            {r.source_attachment_url && (
              <a className="report-link" href="#" style={{ fontSize: 12.5, display: "inline-flex", alignItems: "center", gap: 6 }}>
                <DocIcon />
                View original report
              </a>
            )}
          </div>
        ))}
      </div>
    </AppShell>
  );
}
