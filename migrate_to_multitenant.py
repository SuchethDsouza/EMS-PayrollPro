"""
migrate_to_multitenant.py
─────────────────────────
Run this ONCE to:
1. Rename payroll.db → payroll_demo.db  (becomes the demo database)
2. For each non-demo admin in payroll.db, create payroll_<username>.db
3. Move their account into their own DB with a clean slate

Run from F:\PayrollPRO:
    python migrate_to_multitenant.py
"""
import sqlite3, os, shutil, hashlib

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OLD_DB     = os.path.join(BASE_DIR, "payroll.db")
DEMO_DB    = os.path.join(BASE_DIR, "payroll_demo.db")
DEMO_USERS = {"admin", "hr", "amit"}

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def create_schema(conn):
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
            employee_id INTEGER NOT NULL, date TEXT NOT NULL,
            status TEXT DEFAULT 'Present', check_in TEXT, check_out TEXT
        );
        CREATE TABLE IF NOT EXISTS payroll (
            payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL, month INTEGER NOT NULL,
            year INTEGER NOT NULL, basic_pay REAL DEFAULT 0,
            overtime_pay REAL DEFAULT 0, deductions REAL DEFAULT 0,
            net_salary REAL DEFAULT 0, payment_status TEXT DEFAULT 'Pending'
        );
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL, start_date TEXT NOT NULL,
            end_date TEXT NOT NULL, leave_type TEXT DEFAULT 'Casual',
            reason TEXT, status TEXT DEFAULT 'Pending', applied_on TEXT
        );
        CREATE TABLE IF NOT EXISTS cl_balance (
            cl_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL UNIQUE, year INTEGER NOT NULL,
            total_cl INTEGER DEFAULT 12, used_cl INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS performance (
            perf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL, month INTEGER NOT NULL,
            year INTEGER NOT NULL, punctuality INTEGER DEFAULT 0,
            task_completion INTEGER DEFAULT 0, teamwork INTEGER DEFAULT 0,
            communication INTEGER DEFAULT 0, initiative INTEGER DEFAULT 0,
            overall_rating REAL DEFAULT 0, remarks TEXT, reviewed_by TEXT
        );
        CREATE TABLE IF NOT EXISTS email_log (
            email_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL, recipient_id INTEGER NOT NULL,
            subject TEXT NOT NULL, body TEXT NOT NULL,
            sent_at TEXT, status TEXT DEFAULT 'Sent'
        );
        CREATE TABLE IF NOT EXISTS announcements (
            ann_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, body TEXT, category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'Normal', created_by TEXT,
            created_at TEXT, is_active INTEGER DEFAULT 1
        );
    """)

def seed_departments(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO departments (dept_name, manager) VALUES (?,?)", [
            ("Engineering", ""), ("Human Resources", ""),
            ("Finance", ""),     ("Marketing", ""),
        ])
    conn.commit()

# ── Step 1: Copy payroll.db → payroll_demo.db ─────────────────────────────────
if not os.path.exists(OLD_DB):
    print("❌ payroll.db not found in", BASE_DIR)
    exit(1)

if not os.path.exists(DEMO_DB):
    shutil.copy2(OLD_DB, DEMO_DB)
    print(f"✅ Copied payroll.db → payroll_demo.db")
else:
    print(f"⏭  payroll_demo.db already exists — skipping copy")

# ── Step 2: Find non-demo admin users in old DB ───────────────────────────────
old_conn = sqlite3.connect(OLD_DB, timeout=10)
old_conn.row_factory = sqlite3.Row
all_users = old_conn.execute("SELECT * FROM users").fetchall()
old_conn.close()

real_admins = [u for u in all_users
               if u["username"].lower() not in DEMO_USERS
               and u["role"] == "admin"]

if not real_admins:
    print("\n⚠️  No non-demo admin accounts found in payroll.db.")
    print("   If you registered as 'sucheth', your account may be 'employee' role.")
    print("   Run python fix_self_registered_admins.py first, then re-run this script.")
else:
    print(f"\nFound {len(real_admins)} real admin account(s) to migrate:\n")
    for u in real_admins:
        uname    = u["username"]
        safe     = "".join(c for c in uname.lower() if c.isalnum() or c == "_")
        new_db   = os.path.join(BASE_DIR, f"payroll_{safe}.db")

        if os.path.exists(new_db):
            print(f"  ⏭  {uname} → payroll_{safe}.db already exists, skipping")
            continue

        # Create fresh DB for this admin
        conn = sqlite3.connect(new_db, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        create_schema(conn)
        seed_departments(conn)

        # Insert the admin user
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, status) VALUES (?,?,?,?,?)",
            (uname, u["email"], u["password_hash"], "admin", "Active")
        )
        conn.commit()
        conn.close()
        print(f"  ✅ {uname} → payroll_{safe}.db created (empty, ready for real use)")

print("\n✅ Migration complete!")
print("\nNext steps:")
print("  1. Restart python app.py")
print("  2. Log in as sucheth (or your username) → you'll see an empty admin dashboard")
print("  3. Log in as admin/hr/amit → they still use the demo data")
print("\nYou can safely delete payroll.db later if you want (keep payroll_demo.db).")
