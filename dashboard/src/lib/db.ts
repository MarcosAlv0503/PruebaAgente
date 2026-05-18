/**
 * Read-only Postgres pool for Server Components.
 * All writes go through the agent API (lib/api.ts), never directly from here.
 *
 * Uses a global singleton to survive Next.js hot-reload without exhausting
 * the connection pool.
 */

import { Pool } from "pg";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any as { _pgPool?: Pool };

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

export async function listRecentExecutions(limit = 20): Promise<ExecutionRow[]> {
  const pool = getPool();
  const { rows } = await pool.query<ExecutionRow>(
    `SELECT
       e.id::text                           AS id,
       e.status,
       e.input->>'message'                 AS message,
       e.output->'classification'          AS classification,
       (e.output->>'auto_resolved')::boolean AS auto_resolved,
       c.name                              AS customer_name,
       e.created_at,
       e.finished_at
     FROM executions e
     LEFT JOIN customers c ON c.id = e.customer_id
     ORDER BY e.created_at DESC
     LIMIT $1`,
    [limit],
  );
  return rows;
}
