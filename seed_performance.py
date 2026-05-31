"""
Run this ONCE to seed performance data into payroll_sucheth.db
(or any other admin DB that has employees but no performance records)

Usage:
    python seed_performance.py
    python seed_performance.py alfred        ← for payroll_alfred.db
"""
import sqlite3, os, sys, random, datetime

BASE_DIR = os.path.dirname(__file__)

# ── Pick which DB to seed ──────────────────────────────────────────────────────
username = sys.argv[1] if len(sys.argv) > 1 else "sucheth"
db_path  = os.path.join(BASE_DIR, f"payroll_{username}.db")

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    print(f"   Available DBs: {[f for f in os.listdir(BASE_DIR) if f.endswith('.db')]}")
    sys.exit(1)

conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row

# ── Check existing data ────────────────────────────────────────────────────────
emp_count  = conn.execute("SELECT COUNT(*) FROM employees WHERE status='Active'").fetchone()[0]
perf_count = conn.execute("SELECT COUNT(*) FROM performance").fetchone()[0]

print(f"\n📂 Database : {os.path.basename(db_path)}")
print(f"👥 Active employees : {emp_count}")
print(f"📊 Existing perf rows: {perf_count}")

if emp_count == 0:
    print("❌ No active employees found. Add employees first then run this script.")
    conn.close()
    sys.exit(1)

if perf_count > 0:
    ans = input(f"\n⚠️  {perf_count} performance records already exist. Re-seed anyway? (y/N): ").strip().lower()
    if ans != 'y':
        print("Aborted.")
        conn.close()
        sys.exit(0)
    conn.execute("DELETE FROM performance")
    conn.commit()
    print("🗑  Cleared existing performance data.")

# ── Seed last 6 months for every active employee ──────────────────────────────
today   = datetime.date.today()
emp_ids = [r["employee_id"] for r in
           conn.execute("SELECT employee_id FROM employees WHERE status='Active'").fetchall()]

inserted = 0
for eid in emp_ids:
    for i in range(6):
        m = ((today.month - 1 - i) % 12) + 1
        y = today.year if (today.month - 1 - i) >= 0 else today.year - 1
        p   = random.randint(70, 100)
        tc  = random.randint(65, 100)
        tw  = random.randint(70, 100)
        cm  = random.randint(60, 100)
        ini = random.randint(55, 100)
        overall = round((p + tc + tw + cm + ini) / 5, 1)
        conn.execute("""
            INSERT INTO performance
            (employee_id, month, year, punctuality, task_completion,
             teamwork, communication, initiative, overall_rating, remarks, reviewed_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (eid, m, y, p, tc, tw, cm, ini, overall, "Good performance", "HR Manager"))
        inserted += 1

conn.commit()
conn.close()

print(f"\n✅ Done! Inserted {inserted} performance records")
print(f"   ({len(emp_ids)} employees × 6 months)")
print(f"\n🔄 Restart app.py and check Performance Analytics.")
