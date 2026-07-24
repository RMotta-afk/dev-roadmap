import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { getUserByEmail } from "@/lib/auth-db";
import { verifyPassword } from "@/lib/password";

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await getUserByEmail(credentials.email as string);
        if (!user) {
          return null;
        }

        const valid = await verifyPassword(
          user.passwordHash,
          credentials.password as string
        );
        if (!valid) {
          return null;
        }

        return {
          id: user.id,
          email: user.email,
          name: null,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      // Prefer the standard `sub` claim Auth.js always stores; fall back to our
      // custom `id` for backwards compatibility with older session cookies.
      if (typeof token.sub === "string") {
        session.user.id = token.sub;
      } else if (typeof token.id === "string") {
        session.user.id = token.id;
      }
      if (typeof token.email === "string") {
        session.user.email = token.email;
      }
      return session;
    },
  },
  session: {
    strategy: "jwt",
  },
  secret: process.env.AUTH_SECRET,
});
