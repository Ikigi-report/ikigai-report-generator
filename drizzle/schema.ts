import { index, int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

export const reports = mysqlTable(
  "reports",
  {
    id: int("id").autoincrement().primaryKey(),
    userId: int("userId").notNull(),
    recipientName: varchar("recipientName", { length: 160 }).notNull(),
    secondaryName: varchar("secondaryName", { length: 160 }),
    reportType: mysqlEnum("reportType", ["personal", "compatibility"]).notNull().default("personal"),
    language: mysqlEnum("language", ["en", "ar"]).notNull().default("en"),
    birthDate: varchar("birthDate", { length: 10 }).notNull(),
    birthPlace: text("birthPlace").notNull(),
    status: mysqlEnum("status", ["ready", "failed"]).notNull().default("ready"),
    markdownKey: varchar("markdownKey", { length: 512 }).notNull(),
    calculationsKey: varchar("calculationsKey", { length: 512 }).notNull(),
    pdfKey: varchar("pdfKey", { length: 512 }),
    errorMessage: text("errorMessage"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  table => [index("reports_user_created_idx").on(table.userId, table.createdAt)],
);

export type Report = typeof reports.$inferSelect;
export type InsertReport = typeof reports.$inferInsert;
