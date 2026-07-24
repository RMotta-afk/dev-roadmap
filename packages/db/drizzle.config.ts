import { defineConfig } from "drizzle-kit";
import { config } from "dotenv";
import { resolve } from "node:path";

// Load the monorepo root .env (two levels up from packages/db).
config({ path: resolve(__dirname, "../../.env") });

// The .env DATABASE_URL uses the Python/SQLAlchemy `postgresql+asyncpg://`
// scheme. The JS `postgres` driver only understands `postgresql://`, so strip
// the driver suffix. This points at the Postgres running in the Docker
// container (localhost:5432, user/db `cv_analyzer`).
const databaseUrl = process.env.DATABASE_URL?.replace(
  /^postgresql\+asyncpg:\/\//,
  "postgresql://",
);

if (!databaseUrl) {
  throw new Error("DATABASE_URL is not set");
}

export default defineConfig({
  schema: "./schema.ts",
  out: "./migrations",
  dialect: "postgresql",
  dbCredentials: {
    url: databaseUrl,
  },
});
