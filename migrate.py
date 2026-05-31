import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "payroll.db")

conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row

# Add missing columns to users table
migrations = [
    ("email",         "ALTER TABLE users ADD COLUMN email TEXT"),
    ("reset_token",   "ALTER TABLE users ADD COLUMN reset_token TEXT"),
    ("reset_expires", "ALTER TABLE users ADD COLUMN reset_expires TEXT"),
]

for col_name, sql in migrations:
    try:
        conn.execute(sql)
        print(f"✅ Added column: {col_name}")
    except sqlite3.OperationalError:
        print(f"⏭  Already exists: {col_name}")

# Copy employee emails into users table
conn.execute("""
    UPDATE users SET email = (
        SELECT e.email FROM employees e
        WHERE e.employee_id = users.employee_id
    ) WHERE employee_id IS NOT NULL
""")

# Set admin email manually
conn.execute("UPDATE users SET email='admin@company.com' WHERE username='admin'")

conn.commit()

# Show result
print("\nUsers table after migration:")
rows = conn.execute("SELECT username, email, role FROM users").fetchall()
for r in rows:
    print(f"  {r['username']:12} | {str(r['email']):30} | {r['role']}")

conn.close()
print("\n✅ Migration complete!")