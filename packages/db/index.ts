// Export the postgres-js `db` instance (connects to the Docker Postgres
// container, with monorepo `.env` loading and URL scheme normalization).
export { db } from "./db";

export * as schema from "./schema";
export type { User, NewUser, Analysis, NewAnalysis, AnalysisStatus } from "./schema";
