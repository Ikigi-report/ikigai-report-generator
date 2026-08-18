import { and, desc, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertReport, InsertUser, reports, users } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function createReport(report: InsertReport) {
  const db = await getDb();
  if (!db) throw new Error("Database is unavailable. Please try again shortly.");

  const result = await db.insert(reports).values(report);
  const insertHeader = Array.isArray(result) ? result[0] : result;
  const insertId = Number((insertHeader as { insertId?: number } | undefined)?.insertId);
  if (!insertId) throw new Error("Report record could not be created.");
  return getReportByIdForUser(insertId, report.userId);
}

export async function getReportByIdForUser(reportId: number, userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database is unavailable. Please try again shortly.");
  const rows = await db.select().from(reports).where(and(eq(reports.id, reportId), eq(reports.userId, userId))).limit(1);
  return rows[0] ?? null;
}

export async function listReportsForUser(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database is unavailable. Please try again shortly.");
  return db.select().from(reports).where(eq(reports.userId, userId)).orderBy(desc(reports.createdAt));
}

export async function savePdfKey(reportId: number, userId: number, pdfKey: string) {
  const db = await getDb();
  if (!db) throw new Error("Database is unavailable. Please try again shortly.");
  await db.update(reports).set({ pdfKey }).where(and(eq(reports.id, reportId), eq(reports.userId, userId)));
  return getReportByIdForUser(reportId, userId);
}
