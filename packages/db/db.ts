import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { config } from "dotenv";
import { resolve } from "node:path";
import * as schema from "./schema";

// Load the monorepo root .env (two levels up from packages/db).
config({ path: resolve(__dirname, "../../.env") });

// Normalize the Python/SQLAlchemy `postgresql+asyncpg://` scheme to the plain
// `postgresql://` the JS `postgres` driver expects. Connects to the Postgres
// running in the Docker container.
const connectionString = process.env.DATABASE_URL?.replace(
  /^postgresql\+asyncpg:\/\//,
  "postgresql://",
);

if (!connectionString) {
  throw new Error("DATABASE_URL is not set");
}

const client = postgres(connectionString);
export const db = drizzle(client, { schema });
