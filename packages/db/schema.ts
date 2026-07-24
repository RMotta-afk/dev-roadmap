import { pgTable, uuid, varchar, timestamp, boolean, jsonb } from "drizzle-orm/pg-core";

export const usersTable = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: varchar("email", { length: 255 }).notNull().unique(),
  passwordHash: varchar("password_hash", { length: 255 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  isAdmin: boolean("is_admin").default(false).notNull(),
});

export const analysesTable = pgTable("analyses", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .references(() => usersTable.id),
  request: jsonb("request").notNull(),
  result: jsonb("result"),
  status: varchar("status", { length: 20 })
    .notNull()
    .$type<"running" | "done" | "failed">(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  completedAt: timestamp("completed_at", { withTimezone: true }),
});

export type User = typeof usersTable.$inferSelect;
export type NewUser = typeof usersTable.$inferInsert;
export type Analysis = typeof analysesTable.$inferSelect;
export type NewAnalysis = typeof analysesTable.$inferInsert;
export type AnalysisStatus = "running" | "done" | "failed";
