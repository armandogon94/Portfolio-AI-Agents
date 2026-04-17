/**
 * Server-side share-token mint proxy (slice-27).
 *
 * The backend owns SHARE_SECRET; this Route Handler stays in the Next.js
 * server runtime so the Dashboard API key (if any) never reaches the
 * browser bundle. DEC-26b + slice-27.
 */

import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8060";
const API_KEY = process.env.DASHBOARD_API_KEY;

export async function POST(request: Request) {
  const { task_id } = (await request.json()) as { task_id?: string };
  if (!task_id) {
    return NextResponse.json(
      { error: "task_id is required" },
      { status: 400 },
    );
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const resp = await fetch(`${API_URL}/share/mint`, {
    method: "POST",
    headers,
    body: JSON.stringify({ task_id }),
  });

  if (!resp.ok) {
    const detail = await resp.text().catch(() => resp.statusText);
    return NextResponse.json(
      { error: `Backend refused mint: ${detail}` },
      { status: resp.status },
    );
  }

  const body = (await resp.json()) as {
    token: string;
    url_path: string;
    expires_in: number;
  };
  return NextResponse.json({
    token: body.token,
    url: `${API_URL}${body.url_path}`,
    expires_in: body.expires_in,
  });
}
