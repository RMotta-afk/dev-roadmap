import { auth } from "@/auth";
import { NextResponse } from "next/server";

export const proxy = auth((req) => {
  const isAuthed = Boolean(req.auth?.user?.id && req.auth?.user?.email);
  const isSignIn = req.nextUrl.pathname === "/sign-in";

  if (!isAuthed) {
    if (isSignIn) return NextResponse.next();
    return NextResponse.redirect(new URL("/sign-in", req.nextUrl.origin));
  }

  if (isSignIn) {
    return NextResponse.redirect(new URL("/home", req.nextUrl.origin));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
