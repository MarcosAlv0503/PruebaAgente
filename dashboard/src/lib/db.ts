/**
 * Read-only Postgres pool for Server Components.
 * All writes go through the agent API (lib/api.ts), never directly from here.
 *
 * Uses a global singleton to survive Next.js hot-reload without exhausting
 * the connection pool.
 */

import { Pool } from "pg";
import type { ReportStats, TypeStat, TopicStat } from "./report-types";

const g = globalThis as unknown as { _pgPool?: Pool };

function getPool(): Pool {
  if (!g._pgPool) {
    g._pgPool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 5,
      idleTimeoutMillis: 30_000,
    });
  }
  return g._pgPool;
}

// ---------------------------------------------------------------------------
// Row types
// ---------------------------------------------------------------------------

export interface CustomerRow {
  id: string;
  name: string;
  external_ref: string | null;
}

export interface ExecutionRow {
  id: string;
  status: string;
  message: string | null;
  classification: {
    type?: string;
    severity?: string;
    confidence?: number;
  } | null;
  auto_resolved: boolean | null;
  customer_name: string | null;
  created_at: Date;
  finished_at: Date | null;
  turn_count: number;
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export async function findCustomerById(id: string): Promise<CustomerRow | null> {
  const pool = getPool();
  const { rows } = await pool.query<CustomerRow>(
    "SELECT id::text, name, external_ref FROM customers WHERE id = $1::uuid LIMIT 1",
    [id],
  );
  return rows[0] ?? null;
}

export { type ReportStats } from "./report-types";

// ---------------------------------------------------------------------------
// Report stats
// ---------------------------------------------------------------------------

interface RawStatsRow {
  created_at: Date;
  auto_resolved: string | null;
  incident_type: string | null;
  confidence: number | null;
  kb_refs: string[] | null;
}

export async function getReportStats(): Promise<ReportStats> {
  const pool = getPool();
  const { rows } = await pool.query<RawStatsRow>(`
    WITH first_exec AS (
      SELECT DISTINCT ON (COALESCE(thread_id, id))
        COALESCE(thread_id, id) AS thread_key,
        created_at
      FROM executions
      ORDER BY COALESCE(thread_id, id), created_at ASC
    ),
    last_exec AS (
      SELECT DISTINCT ON (COALESCE(thread_id, id))
        COALESCE(thread_id, id) AS thread_key,
        output
      FROM executions
      ORDER BY COALESCE(thread_id, id), created_at DESC
    )
    SELECT
      fe.created_at,
      le.output->>'auto_resolved'                          AS auto_resolved,
      le.output->'classification'->>'type'                 AS incident_type,
      (le.output->'classification'->>'confidence')::float  AS confidence,
      le.output->'kb_refs'                                 AS kb_refs
    FROM first_exec fe
    JOIN last_exec le ON le.thread_key = fe.thread_key
    WHERE le.output IS NOT NULL
  `);

  let deterministic = 0;
  let lightLlm = 0;
  let heavyLlm = 0;
  let confidenceSum = 0;
  let confidenceCount = 0;
  let highConf = 0;
  let medConf = 0;
  let lowConf = 0;
  let minDate: Date | null = null;
  let maxDate: Date | null = null;

  const typeCounts = new Map<string, { total: number; unresolved: number }>();

  for (const row of rows) {
    const d = new Date(row.created_at);
    if (!minDate || d < minDate) minDate = d;
    if (!maxDate || d > maxDate) maxDate = d;

    const isAutoResolved = row.auto_resolved === "true";
    const hasKbRefs = Array.isArray(row.kb_refs) && row.kb_refs.length > 0;

    if (!isAutoResolved) {
      heavyLlm++;
    } else if (hasKbRefs) {
      lightLlm++;
    } else {
      deterministic++;
    }

    const conf = row.confidence;
    if (conf !== null && !isNaN(conf)) {
      confidenceSum += conf;
      confidenceCount++;
      if (conf > 0.75) highConf++;
      else if (conf >= 0.5) medConf++;
      else lowConf++;
    }

    const type = row.incident_type ?? "unknown";
    const entry = typeCounts.get(type) ?? { total: 0, unresolved: 0 };
    entry.total++;
    if (!isAutoResolved) entry.unresolved++;
    typeCounts.set(type, entry);
  }

  const total = rows.length;

  const typeStats: TypeStat[] = Array.from(typeCounts.entries())
    .map(([type, data]) => ({ type, total: data.total, unresolved: data.unresolved }))
    .sort(
      (a, b) =>
        b.unresolved / Math.max(b.total, 1) - a.unresolved / Math.max(a.total, 1),
    );

  const topTopics: TopicStat[] = Array.from(typeCounts.entries())
    .map(([topic, data]) => ({
      topic,
      count: data.total,
      percent: total > 0 ? Math.round((data.total / total) * 100) : 0,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  return {
    total,
    minDate: minDate?.toISOString() ?? null,
    maxDate: maxDate?.toISOString() ?? null,
    resolutionMethod: { deterministic, lightLlm, heavyLlm },
    confidence: {
      avg: confidenceCount > 0 ? confidenceSum / confidenceCount : null,
      high: highConf,
      medium: medConf,
      low: lowConf,
    },
    typeStats,
    topTopics,
  };
}

export async function listRecentExecutions(limit = 20): Promise<ExecutionRow[]> {
  const pool = getPool();
  const { rows } = await pool.query<ExecutionRow>(
    `SELECT
       root.id::text                              AS id,
       last_exec.status                           AS status,
       root.input->>'message'                     AS message,
       last_exec.output->'classification'         AS classification,
       (last_exec.output->>'auto_resolved')::bool AS auto_resolved,
       c.name                                     AS customer_name,
       root.created_at,
       last_exec.finished_at,
       turns.turn_count
     FROM (
       SELECT DISTINCT ON (COALESCE(thread_id, id))
         id, customer_id, input, created_at,
         COALESCE(thread_id, id) AS thread_key
       FROM executions
       ORDER BY COALESCE(thread_id, id), created_at ASC
     ) root
     JOIN (
       SELECT DISTINCT ON (COALESCE(thread_id, id))
         COALESCE(thread_id, id) AS thread_key,
         status, output, finished_at
       FROM executions
       ORDER BY COALESCE(thread_id, id), created_at DESC
     ) last_exec ON last_exec.thread_key = root.thread_key
     JOIN (
       SELECT COALESCE(thread_id, id) AS thread_key, COUNT(*)::int AS turn_count
       FROM executions
       GROUP BY COALESCE(thread_id, id)
     ) turns ON turns.thread_key = root.thread_key
     LEFT JOIN customers c ON c.id = root.customer_id
     ORDER BY root.created_at DESC
     LIMIT $1`,
    [limit],
  );
  return rows;
}
