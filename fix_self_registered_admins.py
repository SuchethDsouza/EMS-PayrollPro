"""
fix_self_registered_admins.py
─────────────────────────────
Promotes self-registered user accounts (those with no linked employee record)
to the 'admin' role. Run this ONCE to fix existing accounts like 'sucheth'.
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "payroll.db")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Find users who self-registered (no employee_id) but are still 'employee'
candidates = conn.execute("""
    SELECT user_id, username, email, role
    FROM users
    WHERE employee_id IS NULL
      AND role = 'employee'
""").fetchall()

if not candidates:
    print("✅ No accounts need fixing — all self-registered users already have correct roles.")
else:
    print(f"Found {len(candidates)} account(s) to promote:\n")
    print(f"  {'ID':<5} {'Username':<18} {'Email':<30} {'Role':<10}")
    print("  " + "-" * 65)
    for r in candidates:
        print(f"  {r['user_id']:<5} {r['username']:<18} {str(r['email'] or ''):<30} {r['role']}")

    print()
    confirm = input("Promote all above accounts to 'admin'? (yes/no): ").strip().lower()
    if confirm == "yes":
        for r in candidates:
            conn.execute("UPDATE users SET role='admin' WHERE user_id=?", (r['user_id'],))
        conn.commit()
        print("\n✅ Done! Promoted accounts:")
        for r in candidates:
            print(f"   {r['username']} → admin")
        print("\nRestart python app.py and log in — you'll now see the Admin dashboard.")
    else:
        print("Cancelled — no changes made.")

conn.close()
