"use client";

import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  CircleHelp,
  FileText,
  GitBranch,
  ListFilter,
  RefreshCcw,
  Search,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { DashboardLoadResult, DashboardPayload, DashboardRun } from "../lib/types";

type StatusFilter = "all" | "blocked" | "open" | "closed";
const emptyRuns: DashboardRun[] = [];

const statusIcons: Record<string, ReactNode> = {
  closed: <CheckCircle2 aria-hidden="true" size={18} />,
  blocked: <AlertTriangle aria-hidden="true" size={18} />,
  open: <CircleDot aria-hidden="true" size={18} />,
};

export function Dashboard({ initialResult }: { initialResult: DashboardLoadResult }) {
  const [result, setResult] = useState<DashboardLoadResult>(initialResult);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [query, setQuery] = useState("");
  const [selectedPath, setSelectedPath] = useState<string | null>(
    initialResult.ok ? initialResult.payload.runs[0]?.path ?? null : null,
  );
  const [refreshing, setRefreshing] = useState(false);

  const payload = result.ok ? result.payload : null;
  const runs = result.ok ? result.payload.runs : emptyRuns;
  const filteredRuns = useMemo(
    () =>
      runs.filter((run) => {
        const matchesStatus = statusFilter === "all" || run.status === statusFilter;
        const needle = query.trim().toLowerCase();
        const matchesQuery =
          !needle ||
          [
            run.skill_id,
            run.path,
            run.run_id ?? "",
            run.mcp_session_id ?? "",
            run.repository_fingerprint ?? "",
            run.closure_status,
            run.quality_status,
          ]
            .concat(run.missing_information.map((item) => `${item.label} ${item.code}`))
            .join(" ")
            .toLowerCase()
            .includes(needle);
        return matchesStatus && matchesQuery;
      }),
    [query, runs, statusFilter],
  );
  const selectedRun =
    filteredRuns.find((run) => run.path === selectedPath) ?? filteredRuns[0] ?? runs[0] ?? null;

  async function refresh() {
    setRefreshing(true);
    try {
      const response = await fetch("/api/runs", { cache: "no-store" });
      const next = (await response.json()) as DashboardLoadResult;
      setResult(next);
      if (next.ok) {
        setSelectedPath((current) =>
          current && next.payload.runs.some((run) => run.path === current)
            ? current
            : next.payload.runs[0]?.path ?? null,
        );
      }
    } catch (error) {
      setResult({
        ok: false,
        error: "Failed to refresh dashboard data.",
        detail: error instanceof Error ? error.message : String(error),
      });
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <section className="topbar">
        <div>
          <p className="kicker">XRefKit Runtime Observation</p>
          <h1>Skill Run Dashboard</h1>
          <p className="path-line">{payload?.sessions_dir ?? "work/sessions"}</p>
          {payload ? <p className="path-line">MCP audit: {payload.mcp_audit_log}</p> : null}
        </div>
        <button className="icon-button primary" type="button" onClick={refresh} disabled={refreshing} title="Refresh logs">
          <RefreshCcw aria-hidden="true" size={18} />
          <span>{refreshing ? "Refreshing" : "Refresh"}</span>
        </button>
      </section>

      {!result.ok ? (
        <ErrorPanel result={result} />
      ) : (
        <>
          <Summary payload={result.payload} />
          {result.payload.audit_errors.length ? (
            <section className="audit-warning">
              <AlertTriangle aria-hidden="true" size={18} />
              <div>
                <strong>MCP audit log contains unreadable records.</strong>
                {result.payload.audit_errors.slice(0, 5).map((error) => <p key={error}>{error}</p>)}
              </div>
            </section>
          ) : null}
          <section className="workspace">
            <aside className="run-list" aria-label="Skill run list">
              <div className="filters">
                <div className="search-box">
                  <Search aria-hidden="true" size={17} />
                  <input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Search skill, path, status"
                    aria-label="Search skill runs"
                  />
                </div>
                <div className="segmented" aria-label="Status filter">
                  {(["all", "blocked", "open", "closed"] as const).map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={statusFilter === value ? "active" : ""}
                      onClick={() => setStatusFilter(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
              <div className="list-count">
                <ListFilter aria-hidden="true" size={16} />
                <span>{filteredRuns.length} runs</span>
              </div>
              <div className="runs">
                {filteredRuns.map((run) => (
                  <button
                    key={run.path}
                    type="button"
                    className={`run-row ${run.status} ${selectedRun?.path === run.path ? "selected" : ""}`}
                    onClick={() => setSelectedPath(run.path)}
                  >
                    <span className={`status-dot ${run.status}`} />
                    <span className="run-row-main">
                      <strong>{run.skill_id}</strong>
                      <span>{run.path}</span>
                    </span>
                    <span className={`badge ${run.status}`}>{run.status}</span>
                  </button>
                ))}
                {filteredRuns.length === 0 ? <div className="empty">No runs match the current filter.</div> : null}
              </div>
            </aside>

            <section className="detail" aria-label="Selected Skill run detail">
              {selectedRun ? <RunDetail run={selectedRun} payload={result.payload} /> : <div className="empty">No Skill run logs found.</div>}
            </section>
          </section>
        </>
      )}
    </main>
  );
}

function Summary({ payload }: { payload: DashboardPayload }) {
  const metrics = [
    ["Runs", payload.summary.runs, FileText],
    ["Blocked", payload.summary.blocked, AlertTriangle],
    ["Open", payload.summary.open, CircleDot],
    ["Closed", payload.summary.closed, CheckCircle2],
    ["Unknowns", payload.summary.unknowns, ShieldCheck],
    ["Risks", payload.summary.risks, AlertTriangle],
    ["Handoffs", payload.summary.handoffs, GitBranch],
    ["Missing Info", payload.summary.missing_information, CircleHelp],
  ] as const;

  return (
    <section className="metrics" aria-label="Dashboard summary">
      {metrics.map(([label, value, Icon]) => (
        <div className="metric" key={label}>
          <Icon aria-hidden="true" size={18} />
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  );
}

function RunDetail({ run, payload }: { run: DashboardRun; payload: DashboardPayload }) {
  return (
    <article className={`detail-panel ${run.status}`}>
      <header className="detail-head">
        <div>
          <p className="kicker">Selected run</p>
          <h2>{run.skill_id}</h2>
          <p className="path-line">{run.path}</p>
        </div>
        <span className={`detail-status ${run.status}`}>
          {statusIcons[run.status] ?? statusIcons.open}
          {run.status}
        </span>
      </header>

      <section className="detail-grid">
        <InfoBlock label="Closure" value={run.closure_status} />
        <InfoBlock label="Quality" value={run.quality_required ? run.quality_status : `${run.quality_status} optional`} />
        <InfoBlock label="Work Items" value={String(run.counts.work_items ?? 0)} />
        <InfoBlock label="Artifacts" value={String(run.counts.artifacts ?? 0)} />
      </section>

      <Section title="Run Correlation">
        <div className="correlation-grid">
          <InfoBlock label="Run ID" value={run.run_id ?? "not recorded"} />
          <InfoBlock label="MCP Session" value={run.mcp_session_id ?? "not recorded"} />
          <InfoBlock label="Repository" value={run.repository_fingerprint ?? "not recorded"} />
          <InfoBlock label="MCP Events" value={String(run.mcp_events.length)} />
        </div>
      </Section>

      <Section title="Phase State">
        <div className="phase-grid">
          {Object.entries(run.sections).map(([phase, status]) => (
            <div className="phase" key={phase}>
              <span>{phase}</span>
              <strong>{status}</strong>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Blockers">
        {run.blockers.length ? (
          <ul className="plain-list">
            {run.blockers.map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">No blockers recorded by the runtime parser.</p>
        )}
      </Section>

      <Section title="Runtime Records">
        <div className="record-grid">
          <RecordList title="Work" rows={run.work_items} labelKey="item_id" />
          <RecordList title="Artifacts" rows={run.artifacts} labelKey="artifact_id" />
          <RecordList title="Concerns" rows={run.concerns} labelKey="concern_id" />
        </div>
      </Section>

      <Section title="Knowledge XIDs">
        <div className="xid-grid">
          <XidList title="Available" values={run.available_xids} />
          <XidList title="Selected" values={run.selected_xids} />
          <XidList title="Resolved by MCP" values={run.queried_xids} />
          <XidList title="Loaded" values={run.loaded_xids} />
          <XidList title="Used" values={run.used_xids} />
          <XidList title="Unused" values={run.unused_xids} />
        </div>
      </Section>

      <Section title="Knowledge Correlation Gaps">
        <div className="xid-grid correlation-xid-grid">
          <XidList title="Resolved, not loaded" values={run.queried_not_loaded_xids} />
          <XidList title="Loaded, not applied" values={run.loaded_not_applied_xids} />
        </div>
      </Section>

      <Section title="MCP Audit Events">
        {run.mcp_events.length ? (
          <div className="event-list">
            {run.mcp_events.slice(0, 12).map((event, index) => (
              <div className="event-row" key={`${String(event.timestamp ?? event.event_type)}-${index}`}>
                <strong>{String(event.event_type ?? "event")}</strong>
                <span>{String(event.tool ?? "")}</span>
                <code>{String(event.xid ?? event.query ?? event.selected_skill ?? "")}</code>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No correlated MCP events.</p>
        )}
      </Section>

      <Section title="Missing Information">
        {run.missing_information.length ? (
          <div className="missing-list">
            {run.missing_information.map((item) => (
              <div className="missing-item" key={item.code}>
                <CircleHelp aria-hidden="true" size={17} />
                <div>
                  <strong>{item.label}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No missing tuning information detected.</p>
        )}
      </Section>

      <Section title="Missing Information Ranking">
        <div className="ranking">
          {payload.missing_information_ranking.slice(0, 10).map((row) => (
            <div className="ranking-row missing-ranking-row" key={row.code}>
              <span>
                <strong>{row.label}</strong>
                <small>{row.detail}</small>
              </span>
              <span>{row.count} runs</span>
            </div>
          ))}
          {payload.missing_information_ranking.length === 0 ? <p className="muted">No missing tuning information.</p> : null}
        </div>
      </Section>

      <Section title="Unused XID Ranking">
        <div className="ranking">
          {payload.unused_xid_ranking.slice(0, 8).map((row) => (
            <div className="ranking-row" key={row.xid}>
              <strong>{row.xid}</strong>
              <span>{row.count} runs</span>
            </div>
          ))}
          {payload.unused_xid_ranking.length === 0 ? <p className="muted">No unused available XIDs.</p> : null}
        </div>
      </Section>
    </article>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-block">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="detail-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function RecordList({
  title,
  rows,
  labelKey,
}: {
  title: string;
  rows: Array<Record<string, string>>;
  labelKey: string;
}) {
  return (
    <div className="record-list">
      <h4>{title}</h4>
      {rows.slice(0, 6).map((row, index) => (
        <div className="record" key={`${row[labelKey] ?? title}-${index}`}>
          <strong>{row[labelKey] ?? "record"}</strong>
          <span>{row.status ?? row.kind ?? row.role ?? ""}</span>
          <p>{row.text ?? row.note ?? row.target ?? ""}</p>
        </div>
      ))}
      {rows.length === 0 ? <p className="muted">No records.</p> : null}
    </div>
  );
}

function XidList({ title, values }: { title: string; values: string[] }) {
  return (
    <div className="xid-list">
      <h4>{title}</h4>
      <div>
        {values.slice(0, 10).map((value) => (
          <span className="xid" key={value}>
            {value}
          </span>
        ))}
        {values.length === 0 ? <p className="muted">None</p> : null}
      </div>
    </div>
  );
}

function ErrorPanel({ result }: { result: Extract<DashboardLoadResult, { ok: false }> }) {
  return (
    <section className="error-panel">
      <AlertTriangle aria-hidden="true" size={22} />
      <div>
        <h2>{result.error}</h2>
        <pre>{result.detail ?? "No detail returned."}</pre>
      </div>
    </section>
  );
}
