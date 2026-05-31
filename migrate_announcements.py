"""
Run this ONCE to add the announcements table to your existing payroll.db
Usage: python migrate_announcements.py
"""
import sqlite3
import os
import datetime

DB_NAME = os.path.join(os.path.dirname(__file__), "payroll.db")

conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row

# ── Create announcements table ────────────────────────────────────────────────
try:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            ann_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            body        TEXT NOT NULL,
            category    TEXT DEFAULT 'General',
            priority    TEXT DEFAULT 'Normal',
            created_by  TEXT,
            created_at  TEXT,
            is_active   INTEGER DEFAULT 1
        )
    """)
    print("✅ announcements table created")
except sqlite3.OperationalError as e:
    print(f"⚠️  {e}")

# ── Seed 3 sample announcements ───────────────────────────────────────────────
count = conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
if count == 0:
    today = str(datetime.date.today())
    conn.executemany(
        "INSERT INTO announcements (title,body,category,priority,created_by,created_at,is_active) VALUES (?,?,?,?,?,?,?)",
        [
            ("Welcome to PayrollPro!",
             "Our new HR management system is now live. All employees can access their payslips, attendance, and leave records.",
             "General", "High", "admin", today, 1),
            ("Salary Revision Effective June 2026",
             "Annual salary appraisals have been processed. Please check your updated payslip in the system.",
             "Payroll", "High", "hr", today, 1),
            ("Holiday Notice — May 2026",
             "The office will remain closed on May 26th (Monday) for a public holiday. Plan your work accordingly.",
             "General", "Normal", "hr", today, 1),
        ]
    )
    print("✅ 3 sample announcements added")
else:
    print(f"⏭  announcements table already has {count} rows — skipping seed")

conn.commit()
conn.close()
print("\n✅ Migration complete! You can now restart app.py")
