import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { api } from "../api";
import { useHeader } from "../context/AppContext";
import { ChatPanel } from "./ChatPanel";
import { LabsIcon, RefreshIcon, ReportsIcon, SparkleIcon, TrendsIcon } from "../icons";

export function AppShell() {
  const location = useLocation();
  const { title, bumpSyncVersion } = useHeader();
  const [chatOpen, setChatOpen] = useState(false);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [lastSynced, setLastSynced] = useState<string | null>(null);

  useEffect(() => {
    api.authStatus().then((s) => setConnected(s.connected)).catch(() => setConnected(false));
  }, []);

  async function handleSync() {
    setSyncing(true);
    try {
      await api.sync();
      setLastSynced(new Date().toLocaleTimeString());
      bumpSyncVersion();
    } catch {
      alert("Sync failed — check that you're connected to MyChart.");
    } finally {
      setSyncing(false);
    }
  }

  if (connected === false) {
    return (
      <div className="app-shell" style={{ alignItems: "center", justifyContent: "center" }}>
        <div className="card" style={{ maxWidth: 420, textAlign: "center", display: "flex", flexDirection: "column", gap: 16 }}>
          <h1 className="page-title">Connect your MyChart account</h1>
          <p style={{ color: "var(--ink-muted)", fontSize: 14 }}>
            Health Assistant needs a one-time authorization to read your lab results and reports.
          </p>
          <button className="btn-ask-ai" style={{ justifyContent: "center" }} onClick={() => api.login()}>
            Connect MyChart
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <SparkleIcon size={15} />
          </div>
          <div className="brand-name">Health Assistant</div>
        </div>
        <nav className="nav">
          <Link className={`nav-link ${location.pathname === "/" ? "active" : ""}`} to="/">
            <LabsIcon />
            Lab Results
          </Link>
          <Link className={`nav-link ${location.pathname === "/trends" ? "active" : ""}`} to="/trends">
            <TrendsIcon />
            Trends
          </Link>
          <Link className={`nav-link ${location.pathname === "/reports" ? "active" : ""}`} to="/reports">
            <ReportsIcon />
            Reports
          </Link>
        </nav>
        <div className="sync-box">
          <div className="sync-meta">{lastSynced ? `Last synced ${lastSynced}` : "Not synced yet this session"}</div>
          <button className="btn-sync" onClick={handleSync} disabled={syncing}>
            <RefreshIcon />
            {syncing ? "Syncing…" : "Sync now"}
          </button>
        </div>
      </aside>

      <div className="main-content">
        <header className="topbar">
          <h1 className="page-title">{title}</h1>
          <div className="topbar-controls">
            <button className="btn-ask-ai" onClick={() => setChatOpen((v) => !v)}>
              <SparkleIcon />
              Ask about my results
            </button>
          </div>
        </header>
        <div className="content-scroll">
          <Outlet />
        </div>
      </div>

      {chatOpen && <ChatPanel onClose={() => setChatOpen(false)} />}
    </div>
  );
}
