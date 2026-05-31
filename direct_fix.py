"""
direct_fix.py
─────────────
Directly fixes payroll_sucheth.db by checking its contents
and creating the sucheth admin account if it's missing.
Run from F:\PayrollPRO:
    python direct_fix.py
"""
import sqlite3, os, hashlib, glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name TEXT NOT NULL UNIQUE, manager TEXT
        );
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE, phone TEXT,
            position TEXT, department_id INTEGER, base_salary REAL DEFAULT 0,
            join_date TEXT, status TEXT DEFAULT 'Active',
            profile_pic TEXT DEFAULT 'default.png'
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE, email TEXT,
            password_hash TEXT NOT NULL, role TEXT DEFAULT 'employee',
            employee_id INTEGER, status TEXT DEFAULT 'Active',
            reset_token TEXT, reset_expires TEXT
        );
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER, date TEXT, status TEXT,
            check_in TEXT, check_out TEXT
        );
        CREATE TABLE IF NOT EXISTS payroll (
            payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER, month INTEGER, year INTEGER,
            basic_pay REAL DEFAULT 0, overtime_pay REAL DEFAULT 0,
            deductions REAL DEFAULT 0, net_salary REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'Pending'
        );
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER, start_date TEXT, end_date TEXT,
            leave_type TEXT DEFAULT 'Casual', reason TEXT,
            status TEXT DEFAULT 'Pending', applied_on TEXT
        );
        CREATE TABLE IF NOT EXISTS cl_balance (
            cl_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER UNIQUE, year INTEGER,
            total_cl INTEGER DEFAULT 12, used_cl INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS performance (
            perf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER, month INTEGER, year INTEGER,
            punctuality INTEGER DEFAULT 0, task_completion INTEGER DEFAULT 0,
            teamwork INTEGER DEFAULT 0, communication INTEGER DEFAULT 0,
            initiative INTEGER DEFAULT 0, overall_rating REAL DEFAULT 0,
            remarks TEXT, reviewed_by TEXT
        );
        CREATE TABLE IF NOT EXISTS email_log (
            email_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT, recipient_id INTEGER, subject TEXT,
            body TEXT, sent_at TEXT, status TEXT DEFAULT 'Sent'
        );
        CREATE TABLE IF NOT EXISTS announcements (
            ann_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, body TEXT, category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'Normal', created_by TEXT,
            created_at TEXT, is_active INTEGER DEFAULT 1
        );
    """)
    # Seed 4 departments if empty
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT OR IGNORE INTO departments (dept_name, manager) VALUES (?,?)", [
            ("Engineering", ""), ("Human Resources", ""),
            ("Finance", ""),     ("Marketing", ""),
        ])
    conn.commit()

print("=" * 55)
print("  PayrollPro — Direct Login Fix")
print("=" * 55)

# ── Scan ALL .db files ────────────────────────────────────────
all_dbs = sorted(glob.glob(os.path.join(BASE_DIR, "*.db")))
print(f"\nAll databases found in {BASE_DIR}:\n")

for db_path in all_dbs:
    name = os.path.basename(db_path)
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        has_table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if has_table:
            users = conn.execute(
                "SELECT username, email, role, status FROM users"
            ).fetchall()
            if users:
                print(f"  ✅ {name}")
                for u in users:
                    print(f"     → {u['username']:<15} | {str(u['email'] or '(no email)'):<30} | {u['role']} | {u['status'] or 'Active'}")
            else:
                print(f"  ⚠️  {name}  ← EMPTY users table")
        else:
            print(f"  ⚠️  {name}  ← no users table")
        conn.close()
    except Exception as e:
        print(f"  ❌ {name}  ← error: {e}")

# ── Fix payroll_sucheth.db ────────────────────────────────────
print("\n" + "─" * 55)
sucheth_db = os.path.join(BASE_DIR, "payroll_sucheth.db")

if not os.path.exists(sucheth_db):
    print("payroll_sucheth.db does not exist — creating it now...")
    create = True
else:
    conn = sqlite3.connect(sucheth_db, timeout=5)
    conn.row_factory = sqlite3.Row
    has_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    count = 0
    if has_table:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    if count == 0:
        print("payroll_sucheth.db exists but has NO users — fixing now...")
        create = True
    else:
        print("payroll_sucheth.db already has users.")
        create = False

if create:
    username = "sucheth"
    email    = input("\nEnter your email address (e.g. suchethdza@gmail.com): ").strip().lower()
    password = input("Enter your desired password (min 6 chars): ").strip()

    if len(password) < 6:
        print("❌ Password too short. Please use at least 6 characters.")
        exit(1)

    conn = sqlite3.connect(sucheth_db, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    ensure_schema(conn)

    # Remove any old broken user entry
    conn.execute("DELETE FROM users WHERE username=?", (username,))

    # Insert fresh admin account
    conn.execute(
        "INSERT INTO users (username, email, password_hash, role, status) VALUES (?,?,?,?,?)",
        (username, email, hash_password(password), "admin", "Active")
    )
    conn.commit()
    conn.close()

    print(f"\n✅ Account created successfully in payroll_sucheth.db!")
    print(f"\n   Username : {username}")
    print(f"   Password : {password}")
    print(f"   Email    : {email}")
    print(f"   Role     : admin")
    print(f"\n👉 Now restart: python app.py")
    print(f"   Then log in with username: sucheth and your new password.")

else:
    # Offer password reset for existing account
    print("\nWould you like to reset the password for sucheth?")
    yn = input("Type 'yes' to reset, anything else to exit: ").strip().lower()
    if yn == "yes":
        new_pass = input("Enter new password: ").strip()
        conn = sqlite3.connect(sucheth_db, timeout=30)
        conn.execute(
            "UPDATE users SET password_hash=?, status='Active', reset_token=NULL WHERE username='sucheth'",
            (hash_password(new_pass),)
        )
        conn.commit()
        conn.close()
        print(f"\n✅ Password reset for sucheth.")
        print(f"   New password : {new_pass}")
        print(f"\n👉 Restart python app.py and log in!")
