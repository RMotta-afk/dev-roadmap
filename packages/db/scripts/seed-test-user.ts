import { db } from "../db";
import { usersTable } from "../schema";
import { eq } from "drizzle-orm";
import argon2 from "argon2";

/**
 * Seed a default test user for development / demo purposes.
 *
 * Email:    mundo.dev@cv-analyzer.local
 * Password: f3l!pe_p@llm@
 * Name:     Mundo Dev (display name only)
 */

const TEST_USER = {
  email: "mundo.dev@cv-analyzer.local",
  password: "f3l!pe_p@llm@",
  isAdmin: true,
};

async function main() {
  console.log("==> Seeding test user...");

  // Check if user already exists (idempotent)
  const existing = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.email, TEST_USER.email));

  if (existing.length > 0) {
    console.log(`    Test user already exists: ${TEST_USER.email}`);
    console.log("    You can sign in with:");
    console.log(`      Email:    ${TEST_USER.email}`);
    console.log(`      Password: ${TEST_USER.password}`);
    return;
  }

  const passwordHash = await argon2.hash(TEST_USER.password);
  const result = await db
    .insert(usersTable)
    .values({
      email: TEST_USER.email,
      passwordHash,
      isAdmin: TEST_USER.isAdmin,
    })
    .returning({ id: usersTable.id });

  console.log(`    Created test user: ${result[0].id}`);
  console.log("    Sign-in credentials:");
  console.log(`      Email:    ${TEST_USER.email}`);
  console.log(`      Password: ${TEST_USER.password}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
