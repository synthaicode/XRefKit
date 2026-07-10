export type RunStatus = "closed" | "blocked" | "open" | string;

export type MissingInformation = {
  code: string;
  label: string;
  detail: string;
};

export type DashboardRun = {
  path: string;
  name: string;
  mtime: string;
  skill_id: string;
  run_id: string | null;
  mcp_session_id: string | null;
  repository_fingerprint: string | null;
  status: RunStatus;
  closure_status: string;
  quality_required: boolean;
  quality_status: string;
  sections: Record<string, string>;
  counts: Record<string, number>;
  blockers: string[];
  artifacts: Array<Record<string, string>>;
  concerns: Array<Record<string, string>>;
  work_items: Array<Record<string, string>>;
  available_xids: string[];
  selected_xids: string[];
  used_xids: string[];
  unused_xids: string[];
  queried_xids: string[];
  loaded_xids: string[];
  queried_not_loaded_xids: string[];
  loaded_not_applied_xids: string[];
  observation_events: Array<Record<string, unknown>>;
  mcp_events: Array<Record<string, unknown>>;
  missing_information: MissingInformation[];
};

export type DashboardSummary = {
  runs: number;
  closed: number;
  blocked: number;
  open: number;
  unknowns: number;
  risks: number;
  handoffs: number;
  used_xids: number;
  unused_xids: number;
  runs_with_missing_information: number;
  missing_information: number;
};

export type UnusedXidRow = {
  xid: string;
  count: number;
  skills: string[];
  runs: string[];
};

export type MissingInformationRow = MissingInformation & {
  count: number;
  skills: string[];
  runs: string[];
};

export type DashboardPayload = {
  root: string;
  sessions_dir: string;
  mcp_audit_log: string;
  audit_errors: string[];
  summary: DashboardSummary;
  unused_xid_ranking: UnusedXidRow[];
  missing_information_ranking: MissingInformationRow[];
  runs: DashboardRun[];
};

export type DashboardLoadResult =
  | { ok: true; payload: DashboardPayload }
  | { ok: false; error: string; detail?: string };
