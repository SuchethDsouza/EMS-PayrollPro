import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "payroll.db")
conn = sqlite3.connect(DB)

migrations = [
    ("status", "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'Active'"),
]

for col, sql in migrations:
    try:
        conn.execute(sql)
        conn.commit()
        print(f"✅ Added column: {col}")
    except sqlite3.OperationalError:
        print(f"⏭  Already exists: {col}")

# Make sure all existing users are set to Active
conn.execute("UPDATE users SET status = 'Active' WHERE status IS NULL")
conn.commit()

# Confirm
print("\nUsers after migration:")
print(f"{'ID':<5} {'Username':<15} {'Role':<10} {'Status':<10}")
print("-" * 42)
for r in conn.execute("SELECT user_id, username, role, status FROM users"):
    print(f"{r[0]:<5} {r[1]:<15} {r[2]:<10} {r[3]:<10}")

conn.close()
print("\n✅ Migration complete! Now restart python app.py")
