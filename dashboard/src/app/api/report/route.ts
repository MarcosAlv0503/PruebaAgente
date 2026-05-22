import { NextResponse } from "next/server";
import { getReportStats } from "@/lib/db";

export async function GET(): Promise<NextResponse> {
  try {
    const stats = await getReportStats();
    return NextResponse.json(stats);
  } catch {
    return NextResponse.json(
      { error: "No se pudieron obtener los datos del informe" },
      { status: 500 },
    );
  }
}
