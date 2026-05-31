"""
Run this ONCE from F:\PayrollPRO\
Usage: python migrate_gender.py
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Target all .db files that have an employees table
db_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.db')]
print(f"Found {len(db_files)} database(s): {db_files}\n")

for db_file in db_files:
    db_path = os.path.join(BASE_DIR, db_file)
    conn = sqlite3.connect(db_path)

    # Skip DBs with no employees table
    tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"
    ).fetchone()
    if not tbl:
        print(f"SKIP  {db_file} — no employees table")
        conn.close()
        continue

    existing = [row[1] for row in conn.execute("PRAGMA table_info(employees)").fetchall()]
    print(f"DB    {db_file} ({len(existing)} columns)")

    for col, defn in [
        ("gender",           "TEXT DEFAULT ''"),
        ("experience_years", "INTEGER DEFAULT 0"),
    ]:
        if col in existing:
            print(f"      already exists: {col}")
        else:
            try:
                conn.execute(f"ALTER TABLE employees ADD COLUMN {col} {defn}")
                conn.commit()
                print(f"      ADDED: {col}")
            except Exception as e:
                print(f"      ERROR on {col}: {e}")

    # Confirm final columns
    final = [row[1] for row in conn.execute("PRAGMA table_info(employees)").fetchall()]
    print(f"      Final columns: {final}\n")
    conn.close()

print("Done! Restart app.py now.")
