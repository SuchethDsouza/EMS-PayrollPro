"""
create_fresh_admins.py
──────────────────────
Creates a fresh clean database for your real admin account.
Wipes existing payroll_sucheth.db and starts completely clean.

Run from F:\PayrollPRO:
    python create_fresh_admins.py
"""
import sqlite3, os, hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

SCHEMA = """
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
"""

# ── Your real admin account details ──────────────────────────────────────────
DB_FILE  = "payroll_sucheth.db"
USERNAME = "sucheth"
EMAIL    = "suchethdza@gmail.com"
PASSWORD = "sucheth123"

# ── Default departments (you can rename/add more after login) ─────────────────
DEPARTMENTS = [
    "Engineering",
    "Human Resources",
    "Finance",
    "Marketing",
]

print("=" * 55)
print("  PayrollPro — Fresh Real Admin Setup")
print("=" * 55)

db_path = os.path.join(BASE_DIR, DB_FILE)

# Wipe old broken DB
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"\n🗑️  Removed old {DB_FILE}")

# Create fresh DB
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")

# Build schema
conn.executescript(SCHEMA)

# Insert default departments
for dept in DEPARTMENTS:
    conn.execute(
        "INSERT OR IGNORE INTO departments (dept_name, manager) VALUES (?,?)",
        (dept, "")
    )

# Insert your admin account
h = hash_password(PASSWORD)
conn.execute(
    "INSERT INTO users (username, email, password_hash, role, status) VALUES (?,?,?,?,?)",
    (USERNAME, EMAIL, h, "admin", "Active")
)
conn.commit()

# Verify the hash stored correctly
stored = conn.execute(
    "SELECT password_hash FROM users WHERE username=?", (USERNAME,)
).fetchone()[0]
hash_ok = stored == h

conn.close()

print(f"\n✅ Created fresh {DB_FILE}")
print(f"   Username : {USERNAME}")
print(f"   Password : {PASSWORD}")
print(f"   Email    : {EMAIL}")
print(f"   Role     : admin")
print(f"   Hash     : {'✅ OK' if hash_ok else '❌ MISMATCH — contact support'}")
print(f"\n📁 Departments created: {', '.join(DEPARTMENTS)}")
print(f"📋 Employees       : 0  (add them after login)")
print(f"📊 Attendance data : 0  (clean)")
print(f"💰 Payroll data    : 0  (clean)")
print(f"🏖️  Leave data      : 0  (clean)")

print("\n" + "=" * 55)
print("✅ Done! Now restart your app:")
print("     python app.py")
print()
print("Sign in at: http://127.0.0.1:5000/login")
print(f"   Username : {USERNAME}")
print(f"   Password : {PASSWORD}")
print("=" * 55)
