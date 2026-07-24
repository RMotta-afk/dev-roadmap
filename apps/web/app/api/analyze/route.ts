import type { NextAuthRequest } from "next-auth";

import { auth } from "@/auth";
import { mintBackendToken } from "@/lib/backend-token";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const POST = auth(async (req: NextAuthRequest) => {
  if (!req.auth) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const token = await mintBackendToken(req.auth);
  const apiBase = process.env.API_BASE_URL ?? "http://localhost:8000";

  const upstream = await fetch(`${apiBase}/analyze`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: await req.formData(),
  });

  const body = await upstream.text().catch(() => "");

  return new Response(body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: {
      "Content-Type":
        upstream.headers.get("Content-Type") ?? "application/json",
    },
  });
});
