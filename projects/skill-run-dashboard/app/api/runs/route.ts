import { NextResponse } from "next/server";
import { loadDashboardData } from "../../../lib/dashboard-data";

export const dynamic = "force-dynamic";

export async function GET() {
  const result = await loadDashboardData();
  if (!result.ok) {
    return NextResponse.json(result, { status: 500 });
  }
  return NextResponse.json(result);
}
