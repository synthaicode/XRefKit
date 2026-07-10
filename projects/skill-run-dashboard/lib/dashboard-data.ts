import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import type { DashboardLoadResult, DashboardPayload } from "./types";

const execFileAsync = promisify(execFile);

function repoRoot(): string {
  return path.resolve(
    process.env.XREFKIT_ROOT ?? path.join(/* turbopackIgnore: true */ process.cwd(), "..", ".."),
  );
}

function sessionsDir(root: string): string {
  return path.resolve(process.env.XREFKIT_SESSIONS_DIR ?? path.join(root, "work", "sessions"));
}

function mcpAuditLog(root: string): string {
  return path.resolve(
    process.env.XREFKIT_MCP_AUDIT_LOG ?? path.join(root, "work", "mcp", "xid_audit.jsonl"),
  );
}

function pythonCommand(): string {
  return process.env.PYTHON?.trim() || "python";
}

export async function loadDashboardData(): Promise<DashboardLoadResult> {
  const root = repoRoot();
  const sessions = sessionsDir(root);
  const auditLog = mcpAuditLog(root);
  const env = {
    ...process.env,
    PYTHONPATH: [root, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
  };

  try {
    const { stdout } = await execFileAsync(
      pythonCommand(),
      [
        "-m", "xrefkit", "dashboard", "data",
        "--root", root,
        "--sessions-dir", sessions,
        "--mcp-audit-log", auditLog,
      ],
      {
        cwd: root,
        env,
        maxBuffer: 10 * 1024 * 1024,
        timeout: 15000,
      },
    );
    return { ok: true, payload: JSON.parse(stdout) as DashboardPayload };
  } catch (error) {
    const detail =
      error instanceof Error && "stderr" in error
        ? String((error as Error & { stderr?: unknown }).stderr || error.message)
        : error instanceof Error
          ? error.message
          : String(error);
    return {
      ok: false,
      error: "Failed to load XRefKit dashboard data.",
      detail,
    };
  }
}
