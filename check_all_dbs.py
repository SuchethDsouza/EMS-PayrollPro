"""
check_all_dbs.py
────────────────
Shows every user in every database file.
Helps identify which DB still has the old password.

Run from F:\PayrollPRO:
    python check_all_dbs.py
"""
import sqlite3, os, glob, hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Test both passwords
TEST_PASSWORDS = ["sucheth123", "sucheth1234"]

db_files = sorted(glob.glob(os.path.join(BASE_DIR, "payroll_*.db")))

print("=" * 60)
print("  PayrollPro — Database User Inspector")
print("=" * 60)

for db_path in db_files:
    name = os.path.basename(db_path)
    print(f"\n📄 {name}")
    print("-" * 50)
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        users = conn.execute(
            "SELECT user_id, username, email, role, password_hash FROM users"
        ).fetchall()
        conn.close()

        if not users:
            print("  (no users)")
            continue

        for u in users:
            print(f"  ID:{u['user_id']}  {u['username']:15} [{u['role']:8}]  {u['email'] or '(no email)'}")
            # Check which passwords match
            for pwd in TEST_PASSWORDS:
                if hash_password(pwd) == u['password_hash']:
                    print(f"    ⚠️  Password '{pwd}' MATCHES this account")

    except Exception as e:
        print(f"  Error reading: {e}")

print("\n" + "=" * 60)
