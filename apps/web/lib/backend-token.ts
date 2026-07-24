import "server-only";

import { SignJWT } from "jose";
import type { Session } from "next-auth";

const EXPIRY = "15m";

export async function mintBackendToken(session: Session): Promise<string> {
  if (!session.user?.id || !session.user?.email) {
    throw new Error("Session is missing user id or email");
  }

  const secret = process.env.AUTH_BACKEND_SECRET;
  if (!secret) {
    throw new Error("AUTH_BACKEND_SECRET is not configured");
  }

  return new SignJWT({
    email: session.user.email,
    is_admin: false,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(session.user.id)
    .setIssuedAt()
    .setExpirationTime(EXPIRY)
    .sign(new TextEncoder().encode(secret));
}
