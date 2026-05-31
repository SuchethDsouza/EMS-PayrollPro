"""
reset_admin_password.py
───────────────────────
Resets the password for any admin account in their own DB file.
Run from F:\PayrollPRO:
    python reset_admin_password.py
"""
import sqlite3, os, hashlib, glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Find all non-demo admin DB files
db_files = sorted(glob.glob(os.path.join(BASE_DIR, "payroll_*.db")))
demo_db  = os.path.join(BASE_DIR, "payroll_demo.db")

real_dbs = [f for f in db_files if f != demo_db and os.path.exists(f)]

if not real_dbs:
    print("❌ No real admin databases found.")
    print("   Expected files like payroll_sucheth.db in:", BASE_DIR)
    exit(1)

print("Found admin databases:\n")
all_users = []
for db_path in real_dbs:
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        users = conn.execute("SELECT user_id, username, email, role FROM users").fetchall()
        conn.close()
        for u in users:
            all_users.append((db_path, dict(u)))
            print(f"  DB: {os.path.basename(db_path)}")
            print(f"  ID: {u['user_id']}  Username: {u['username']}  Role: {u['role']}")
            print()
    except Exception as e:
        print(f"  ⚠️  Could not read {os.path.basename(db_path)}: {e}")

if not all_users:
    print("❌ No users found in any real DB.")
    exit(1)

print("─" * 40)
username = input("Enter username to reset password for: ").strip().lower()
new_pass = input("Enter new password (min 6 chars): ").strip()

if len(new_pass) < 6:
    print("❌ Password too short.")
    exit(1)

# Find the user across all real DBs
found = False
for db_path, u in all_users:
    if u["username"].lower() == username:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("UPDATE users SET password_hash=? WHERE username=?",
                     (hash_password(new_pass), username))
        conn.commit()
        conn.close()
        print(f"\n✅ Password for '{username}' reset successfully in {os.path.basename(db_path)}")
        print(f"   New password: {new_pass}")
        print(f"\nRestart python app.py and log in with your new password.")
        found = True
        break

if not found:
    print(f"\n❌ Username '{username}' not found in any real admin database.")
    print("   Make sure you ran migrate_to_multitenant.py first.")
