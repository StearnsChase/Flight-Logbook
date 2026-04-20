import { NextResponse } from "next/server";
import { getApiHealth } from "@/lib/api";

export async function GET() {
  const health = await getApiHealth();
  return NextResponse.json({ ok: Boolean(health) });
}
