import sqlite3
import hashlib
import os
import datetime
import random
import calendar

# ── Base directory where all .db files live ───────────────────────────────────
BASE_DIR = os.path.dirname(__file__)

# Legacy single-DB name kept for setup_database() only
DB_NAME  = os.path.join(BASE_DIR, "payroll.db")

# ── Demo DB — always fixed, never changes ─────────────────────────────────────
DEMO_DB  = os.path.join(BASE_DIR, "payroll_demo.db")


def get_db_path(username=None):
    """
    Return the correct .db file path for a given username.
    Demo accounts (admin, hr, amit) always use payroll_demo.db.
    Every other user gets their own payroll_<username>.db file.
    Falls back to reading Flask session if username not passed.
    """
    DEMO_USERS = {"admin", "hr", "amit"}

    if username is None:
        try:
            from flask import session
            # db_owner is the canonical key — set on login to the DB file owner
            username = session.get("db_owner") or session.get("username", "")
        except RuntimeError:
            return DEMO_DB

    if not username or username.lower() in DEMO_USERS:
        return DEMO_DB

    safe = "".join(c for c in username.lower() if c.isalnum() or c == "_")
    return os.path.join(BASE_DIR, f"payroll_{safe}.db")


def get_connection(username=None):
    """
    Open a connection to the correct database for the current user.
    All 52 existing `get_connection()` calls work unchanged — they
    automatically pick up the right DB via Flask session.
    """
    db_path = get_db_path(username)
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _create_schema(conn):
    """Create all tables in the given connection's database."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name       TEXT NOT NULL UNIQUE,
            manager         TEXT
        );

        CREATE TABLE IF NOT EXISTS employees (
            employee_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE,
            phone           TEXT,
            position        TEXT,
            department_id   INTEGER,
            base_salary     REAL DEFAULT 0,
            join_date       TEXT,
            status          TEXT DEFAULT 'Active',
            profile_pic     TEXT DEFAULT 'default.png',
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            email           TEXT,
            password_hash   TEXT NOT NULL,
            role            TEXT DEFAULT 'employee',
            employee_id     INTEGER,
            status          TEXT DEFAULT 'Active',
            reset_token     TEXT,
            reset_expires   TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            date            TEXT NOT NULL,
            status          TEXT DEFAULT 'Present',
            check_in        TEXT,
            check_out       TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS payroll (
            payroll_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            month           INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            basic_pay       REAL DEFAULT 0,
            overtime_pay    REAL DEFAULT 0,
            deductions      REAL DEFAULT 0,
            net_salary      REAL DEFAULT 0,
            payment_status  TEXT DEFAULT 'Pending',
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS leaves (
            leave_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            start_date      TEXT NOT NULL,
            end_date        TEXT NOT NULL,
            leave_type      TEXT DEFAULT 'Casual',
            reason          TEXT,
            status          TEXT DEFAULT 'Pending',
            applied_on      TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS cl_balance (
            cl_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL UNIQUE,
            year            INTEGER NOT NULL,
            total_cl        INTEGER DEFAULT 12,
            used_cl         INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS performance (
            perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            month           INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            punctuality     INTEGER DEFAULT 0,
            task_completion INTEGER DEFAULT 0,
            teamwork        INTEGER DEFAULT 0,
            communication   INTEGER DEFAULT 0,
            initiative      INTEGER DEFAULT 0,
            overall_rating  REAL DEFAULT 0,
            remarks         TEXT,
            reviewed_by     TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS email_log (
            email_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender          TEXT NOT NULL,
            recipient_id    INTEGER NOT NULL,
            subject         TEXT NOT NULL,
            body            TEXT NOT NULL,
            sent_at         TEXT,
            status          TEXT DEFAULT 'Sent',
            FOREIGN KEY (recipient_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS announcements (
            ann_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            body            TEXT,
            category        TEXT DEFAULT 'General',
            priority        TEXT DEFAULT 'Normal',
            created_by      TEXT,
            created_at      TEXT,
            is_active       INTEGER DEFAULT 1
        );
    """)


def _seed_demo_data(conn):
    """Seed demo employees, users, attendance, performance into the given conn."""
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO departments (dept_name, manager) VALUES (?,?)", [
            ("Engineering",    "Ravi Kumar"),
            ("Human Resources","Priya Sharma"),
            ("Finance",        "Anil Verma"),
            ("Marketing",      "Sneha Patel"),
        ])

    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        employees = [
            ("Amit Singh",    "amit@company.com",   "9876543210", "Developer",       1, 55000, "2022-01-15", "Active"),
            ("Divya Nair",    "divya@company.com",  "9876543211", "HR Executive",    2, 42000, "2021-06-01", "Active"),
            ("Rohan Mehta",   "rohan@company.com",  "9876543212", "Accountant",      3, 48000, "2020-03-10", "Active"),
            ("Kavya Reddy",   "kavya@company.com",  "9876543213", "Sr. Developer",   1, 68000, "2019-11-20", "Active"),
            ("Suresh Iyer",   "suresh@company.com", "9876543214", "Marketing Lead",  4, 52000, "2023-02-28", "Active"),
            ("Pooja Ghosh",   "pooja@company.com",  "9876543215", "Team Lead",       1, 72000, "2018-07-05", "Active"),
            ("Manoj Tiwari",  "manoj@company.com",  "9876543216", "Finance Manager", 3, 65000, "2020-09-14", "Active"),
            ("Ananya Das",    "ananya@company.com", "9876543217", "HR Manager",      2, 58000, "2021-12-01", "Active"),
            ("Vikram Joshi",  "vikram@company.com", "9876543218", "Developer",       1, 50000, "2023-05-15", "Active"),
            ("Neha Kulkarni", "neha@company.com",   "9876543219", "Marketing Exec",  4, 45000, "2022-08-20", "Active"),
        ]
        c.executemany(
            "INSERT INTO employees (name,email,phone,position,department_id,base_salary,join_date,status) VALUES (?,?,?,?,?,?,?,?)",
            employees
        )

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username,password_hash,role,employee_id,status) VALUES (?,?,?,?,?)",
                  ("admin", hash_password("admin123"), "admin", None, "Active"))
        c.execute("INSERT INTO users (username,password_hash,role,employee_id,status) VALUES (?,?,?,?,?)",
                  ("hr", hash_password("hr123"), "hr", 2, "Active"))
        c.execute("SELECT employee_id, name FROM employees")
        for row in c.fetchall():
            uname = row["name"].split()[0].lower()
            c.execute("INSERT OR IGNORE INTO users (username,password_hash,role,employee_id,status) VALUES (?,?,?,?,?)",
                      (uname, hash_password("emp123"), "employee", row["employee_id"], "Active"))

    year = datetime.date.today().year
    c.execute("SELECT COUNT(*) FROM cl_balance")
    if c.fetchone()[0] == 0:
        c.execute("SELECT employee_id FROM employees")
        for row in c.fetchall():
            c.execute("INSERT OR IGNORE INTO cl_balance (employee_id,year,total_cl,used_cl) VALUES (?,?,12,0)",
                      (row["employee_id"], year))

    c.execute("SELECT COUNT(*) FROM attendance")
    if c.fetchone()[0] == 0:
        today = datetime.date.today()
        statuses = ["Present"] * 18 + ["Absent"] * 3 + ["Leave"] * 2
        c.execute("SELECT employee_id FROM employees")
        emp_ids = [r[0] for r in c.fetchall()]
        for eid in emp_ids:
            for day in range(1, today.day + 1):
                try:
                    d = datetime.date(today.year, today.month, day)
                    if d.weekday() < 5:
                        st = random.choice(statuses)
                        ci = f"0{random.randint(8,9)}:{random.choice(['00','15','30','45'])}" if st == "Present" else None
                        co = f"1{random.randint(7,8)}:{random.choice(['00','15','30','45'])}" if st == "Present" else None
                        c.execute("INSERT INTO attendance (employee_id,date,status,check_in,check_out) VALUES (?,?,?,?,?)",
                                  (eid, str(d), st, ci, co))
                except Exception:
                    pass

    c.execute("SELECT COUNT(*) FROM performance")
    if c.fetchone()[0] == 0:
        today = datetime.date.today()
        c.execute("SELECT employee_id FROM employees")
        emp_ids = [r[0] for r in c.fetchall()]
        for eid in emp_ids:
            for i in range(6):
                m = ((today.month - 1 - i) % 12) + 1
                y = today.year if today.month - 1 - i >= 0 else today.year - 1
                p  = random.randint(70, 100)
                tc = random.randint(65, 100)
                tw = random.randint(70, 100)
                cm = random.randint(60, 100)
                ini = random.randint(55, 100)
                overall = round((p + tc + tw + cm + ini) / 5, 1)
                c.execute("""INSERT INTO performance
                    (employee_id,month,year,punctuality,task_completion,teamwork,
                     communication,initiative,overall_rating,remarks,reviewed_by)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (eid, m, y, p, tc, tw, cm, ini, overall, "Good performance", "HR Manager"))

    conn.commit()


def setup_database():
    """Set up the demo database (called on app startup)."""
    conn = sqlite3.connect(DEMO_DB, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    _create_schema(conn)
    _seed_demo_data(conn)
    conn.close()
    print(f"✅ Demo database ready: {os.path.basename(DEMO_DB)}")


def setup_new_admin_db(username):
    """
    Create a fresh empty database for a new admin (company owner).
    Called from the register route when a new admin signs up.
    Returns the db path created.
    """
    db_path = get_db_path(username)
    if os.path.exists(db_path):
        return db_path  # already exists, don't overwrite

    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    _create_schema(conn)

    # Seed only the 4 base departments — no employees, no demo data
    c = conn.cursor()
    c.executemany("INSERT INTO departments (dept_name, manager) VALUES (?,?)", [
        ("Engineering",    ""),
        ("Human Resources",""),
        ("Finance",        ""),
        ("Marketing",      ""),
    ])
    conn.commit()
    conn.close()
    print(f"✅ New admin database created: {os.path.basename(db_path)}")
    return db_path


if __name__ == "__main__":
    setup_database()

    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name       TEXT NOT NULL UNIQUE,
            manager         TEXT
        );

        CREATE TABLE IF NOT EXISTS employees (
            employee_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE,
            phone           TEXT,
            position        TEXT,
            department_id   INTEGER,
            base_salary     REAL DEFAULT 0,
            join_date       TEXT,
            status          TEXT DEFAULT 'Active',
            profile_pic     TEXT DEFAULT 'default.png',
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            email           TEXT,
            password_hash   TEXT NOT NULL,
            role            TEXT DEFAULT 'employee',
            employee_id     INTEGER,
            reset_token     TEXT,
            reset_expires   TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            date            TEXT NOT NULL,
            status          TEXT DEFAULT 'Present',
            check_in        TEXT,
            check_out       TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS payroll (
            payroll_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            month           INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            basic_pay       REAL DEFAULT 0,
            overtime_pay    REAL DEFAULT 0,
            deductions      REAL DEFAULT 0,
            net_salary      REAL DEFAULT 0,
            payment_status  TEXT DEFAULT 'Pending',
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS leaves (
            leave_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            start_date      TEXT NOT NULL,
            end_date        TEXT NOT NULL,
            leave_type      TEXT DEFAULT 'Casual',
            reason          TEXT,
            status          TEXT DEFAULT 'Pending',
            applied_on      TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS cl_balance (
            cl_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL UNIQUE,
            year            INTEGER NOT NULL,
            total_cl        INTEGER DEFAULT 12,
            used_cl         INTEGER DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS performance (
            perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER NOT NULL,
            month           INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            punctuality     INTEGER DEFAULT 0,
            task_completion INTEGER DEFAULT 0,
            teamwork        INTEGER DEFAULT 0,
            communication   INTEGER DEFAULT 0,
            initiative      INTEGER DEFAULT 0,
            overall_rating  REAL DEFAULT 0,
            remarks         TEXT,
            reviewed_by     TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS email_log (
            email_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sender          TEXT NOT NULL,
            recipient_id    INTEGER NOT NULL,
            subject         TEXT NOT NULL,
            body            TEXT NOT NULL,
            sent_at         TEXT,
            status          TEXT DEFAULT 'Sent',
            FOREIGN KEY (recipient_id) REFERENCES employees(employee_id)
        );
    """)

    # ── Departments ──────────────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO departments (dept_name, manager) VALUES (?,?)", [
            ("Engineering",    "Ravi Kumar"),
            ("Human Resources","Priya Sharma"),
            ("Finance",        "Anil Verma"),
            ("Marketing",      "Sneha Patel"),
        ])

    # ── Employees ────────────────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        employees = [
            ("Amit Singh",    "amit@company.com",   "9876543210", "Developer",       1, 55000, "2022-01-15", "Active"),
            ("Divya Nair",    "divya@company.com",  "9876543211", "HR Executive",    2, 42000, "2021-06-01", "Active"),
            ("Rohan Mehta",   "rohan@company.com",  "9876543212", "Accountant",      3, 48000, "2020-03-10", "Active"),
            ("Kavya Reddy",   "kavya@company.com",  "9876543213", "Sr. Developer",   1, 68000, "2019-11-20", "Active"),
            ("Suresh Iyer",   "suresh@company.com", "9876543214", "Marketing Lead",  4, 52000, "2023-02-28", "Active"),
            ("Pooja Ghosh",   "pooja@company.com",  "9876543215", "Team Lead",       1, 72000, "2018-07-05", "Active"),
            ("Manoj Tiwari",  "manoj@company.com",  "9876543216", "Finance Manager", 3, 65000, "2020-09-14", "Active"),
            ("Ananya Das",    "ananya@company.com", "9876543217", "HR Manager",      2, 58000, "2021-12-01", "Active"),
            ("Vikram Joshi",  "vikram@company.com", "9876543218", "Developer",       1, 50000, "2023-05-15", "Active"),
            ("Neha Kulkarni", "neha@company.com",   "9876543219", "Marketing Exec",  4, 45000, "2022-08-20", "Active"),
        ]
        c.executemany(
            "INSERT INTO employees (name,email,phone,position,department_id,base_salary,join_date,status) VALUES (?,?,?,?,?,?,?,?)",
            employees
        )

    # ── Users (admin + hr + employee accounts) ────────────────────────────────
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username,password_hash,role,employee_id) VALUES (?,?,?,?)",
                  ("admin", hash_password("admin123"), "admin", None))
        c.execute("INSERT INTO users (username,password_hash,role,employee_id) VALUES (?,?,?,?)",
                  ("hr", hash_password("hr123"), "hr", 2))
        # employee logins
        c.execute("SELECT employee_id, name FROM employees")
        for row in c.fetchall():
            uname = row["name"].split()[0].lower()
            c.execute("INSERT OR IGNORE INTO users (username,password_hash,role,employee_id) VALUES (?,?,?,?)",
                      (uname, hash_password("emp123"), "employee", row["employee_id"]))

    # ── CL Balance ───────────────────────────────────────────────────────────
    year = datetime.date.today().year
    c.execute("SELECT COUNT(*) FROM cl_balance")
    if c.fetchone()[0] == 0:
        c.execute("SELECT employee_id FROM employees")
        for row in c.fetchall():
            c.execute(
                "INSERT OR IGNORE INTO cl_balance (employee_id,year,total_cl,used_cl) VALUES (?,?,12,0)",
                (row["employee_id"], year)
            )

    # ── Attendance (sample) ──────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM attendance")
    if c.fetchone()[0] == 0:
        today = datetime.date.today()
        statuses = ["Present"] * 18 + ["Absent"] * 3 + ["Leave"] * 2
        c.execute("SELECT employee_id FROM employees")
        emp_ids = [r[0] for r in c.fetchall()]
        for eid in emp_ids:
            for day in range(1, today.day + 1):
                try:
                    d = datetime.date(today.year, today.month, day)
                    if d.weekday() < 5:
                        st = random.choice(statuses)
                        ci = f"0{random.randint(8,9)}:{random.choice(['00','15','30','45'])}" if st == "Present" else None
                        co = f"1{random.randint(7,8)}:{random.choice(['00','15','30','45'])}" if st == "Present" else None
                        c.execute(
                            "INSERT INTO attendance (employee_id,date,status,check_in,check_out) VALUES (?,?,?,?,?)",
                            (eid, str(d), st, ci, co)
                        )
                except Exception:
                    pass

    # ── Performance (sample data for last 6 months) ──────────────────────────
    c.execute("SELECT COUNT(*) FROM performance")
    if c.fetchone()[0] == 0:
        today = datetime.date.today()
        c.execute("SELECT employee_id FROM employees")
        emp_ids = [r[0] for r in c.fetchall()]
        for eid in emp_ids:
            for i in range(6):
                m = ((today.month - 1 - i) % 12) + 1
                y = today.year if today.month - 1 - i >= 0 else today.year - 1
                p  = random.randint(70, 100)
                tc = random.randint(65, 100)
                tw = random.randint(70, 100)
                cm = random.randint(60, 100)
                ini = random.randint(55, 100)
                overall = round((p + tc + tw + cm + ini) / 5, 1)
                c.execute("""
                    INSERT INTO performance
                    (employee_id,month,year,punctuality,task_completion,teamwork,communication,initiative,overall_rating,remarks,reviewed_by)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (eid, m, y, p, tc, tw, cm, ini, overall, "Good performance", "HR Manager"))

    conn.commit()
    conn.close()
    print("✅ Database ready: payroll.db")

if __name__ == "__main__":
    setup_database()
