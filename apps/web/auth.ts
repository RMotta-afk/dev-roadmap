import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        // Stub: accept any email/password and return a mock user.
        // Real DB lookup will be wired in later (G4 / T4.2).
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        return {
          id: "mock-user-id",
          email: credentials.email as string,
          name: "Mock User",
        };
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  secret: process.env.AUTH_SECRET,
});
