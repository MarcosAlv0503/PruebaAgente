/**
 * Server-side API client for the agent backend.
 * Used by Next.js Route Handlers and Server Components — not called directly
 * from the browser (AGENT_API_URL may be an internal Docker network address).
 */

const AGENT_API_URL = process.env.AGENT_API_URL ?? "http://localhost:8000";

export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
}

export interface IncidentPayload {
  message: string;
  customer_id: string;
  external_id: string;
  reported_at: string;
  reporter: string;
  channel: "web";
  thread_id?: string;
  conversation_history?: ConversationTurn[];
}

export interface ExecutionQueued {
  execution_id: string;
  thread_id: string;
  status: string;
}

export interface Classification {
  type?: string;
  severity?: string;
  confidence?: number;
}

export interface ExecutionOutput {
  auto_resolved?: boolean;
  classification?: Classification;
  final_response?: string;
  ticket_ref?: string;
  log_ref?: string;
}

export interface ExecutionStatus {
  execution_id: string;
  status: "pending" | "running" | "succeeded" | "failed" | "cancelled";
  output: ExecutionOutput | null;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export async function submitIncident(
  payload: IncidentPayload,
): Promise<ExecutionQueued> {
  const res = await fetch(`${AGENT_API_URL}/api/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Error al enviar incidencia: ${res.status} — ${text}`);
  }
  return res.json() as Promise<ExecutionQueued>;
}

export async function fetchIncidentStatus(
  executionId: string,
): Promise<ExecutionStatus> {
  const res = await fetch(`${AGENT_API_URL}/api/incidents/${executionId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Error al consultar estado: ${res.status}`);
  }
  return res.json() as Promise<ExecutionStatus>;
}
