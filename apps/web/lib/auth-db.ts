import { db, schema } from "@cv-analyzer/db";
import { eq } from "drizzle-orm";

const { usersTable } = schema;

export async function getUserByEmail(email: string) {
  const result = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.email, email))
    .limit(1);

  return result[0] ?? null;
}
