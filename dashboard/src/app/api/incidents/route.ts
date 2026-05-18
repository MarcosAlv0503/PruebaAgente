import { type NextRequest, NextResponse } from "next/server";
import { submitIncident, type IncidentPayload } from "@/lib/api";

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const payload = (await request.json()) as IncidentPayload;
    const result = await submitIncident(payload);
    return NextResponse.json(result, { status: 202 });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Error interno del servidor";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
