import type { NextAuthRequest } from "next-auth";

import { auth } from "@/auth";
import { mintBackendToken } from "@/lib/backend-token";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const GET = auth(async (req: NextAuthRequest) => {
  if (!req.auth) {
    return new Response("Unauthorized", { status: 401 });
  }

  const id = req.nextUrl.pathname.match(/\/analyze\/([^/]+)\/events$/)?.[1];
  if (!id) {
    return new Response("Bad request: missing analysis id", { status: 400 });
  }

  const token = await mintBackendToken(req.auth);
  const apiBase = process.env.API_BASE_URL ?? "http://localhost:8000";

  const upstream = await fetch(`${apiBase}/analyze/${id}/events`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "text/event-stream",
    },
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(upstream.statusText || "Upstream error", {
      status: upstream.status || 502,
    });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
});
