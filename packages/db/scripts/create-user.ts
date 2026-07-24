import { db } from "../db";
import { usersTable } from "../schema";
import { eq } from "drizzle-orm";
import argon2 from "argon2";
import readline from "readline";

async function prompt(question: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

async function main() {
  const args = process.argv.slice(2);
  let email = args[0];
  let password = args[1];

  if (!email) {
    email = await prompt("Email: ");
  }
  if (!password) {
    password = await prompt("Password: ");
  }

  if (!email || !password) {
    console.error("Email and password are required.");
    process.exit(1);
  }

  const existing = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.email, email));

  if (existing.length > 0) {
    console.error(`User with email ${email} already exists.`);
    process.exit(1);
  }

  const passwordHash = await argon2.hash(password);
  const result = await db
    .insert(usersTable)
    .values({
      email,
      passwordHash,
    })
    .returning({ id: usersTable.id });

  console.log(`Created user ${result[0].id}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
