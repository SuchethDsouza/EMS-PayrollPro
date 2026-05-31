import calendar
import datetime
from database import get_connection

def calculate_payroll(employee_id, month, year):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT base_salary FROM employees WHERE employee_id=?", (employee_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    base_salary = row["base_salary"]
    total_days = calendar.monthrange(year, month)[1]
    working_days = sum(1 for d in range(1, total_days+1)
                       if datetime.date(year, month, d).weekday() < 5)
    c.execute("""
        SELECT status FROM attendance
        WHERE employee_id=? AND strftime('%m',date)=? AND strftime('%Y',date)=?
    """, (employee_id, f"{month:02d}", str(year)))
    records  = c.fetchall()
    present  = sum(1 for r in records if r["status"] == "Present")
    absent   = sum(1 for r in records if r["status"] == "Absent")
    daily    = base_salary / working_days if working_days else 0
    basic    = daily * present
    overtime = 0.0
    deduct   = daily * absent
    net      = basic + overtime - deduct
    c.execute("SELECT payroll_id FROM payroll WHERE employee_id=? AND month=? AND year=?",
              (employee_id, month, year))
    ex = c.fetchone()
    if ex:
        c.execute("UPDATE payroll SET basic_pay=?,overtime_pay=?,deductions=?,net_salary=? WHERE payroll_id=?",
                  (round(basic,2), round(overtime,2), round(deduct,2), round(net,2), ex["payroll_id"]))
    else:
        c.execute("INSERT INTO payroll (employee_id,month,year,basic_pay,overtime_pay,deductions,net_salary) VALUES (?,?,?,?,?,?,?)",
                  (employee_id, month, year, round(basic,2), round(overtime,2), round(deduct,2), round(net,2)))
    conn.commit()
    conn.close()
    return dict(base_salary=base_salary, working_days=working_days,
                present_days=present, absent_days=absent,
                daily_rate=round(daily,2), basic_pay=round(basic,2),
                overtime_pay=round(overtime,2), deductions=round(deduct,2),
                net_salary=round(net,2))

def calculate_all_payroll(month, year):
    conn = get_connection()
    ids = [r["employee_id"] for r in conn.execute("SELECT employee_id FROM employees WHERE status='Active'").fetchall()]
    conn.close()
    for eid in ids:
        calculate_payroll(eid, month, year)

def get_payroll_summary(month, year):
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.name, d.dept_name, p.basic_pay, p.deductions, p.net_salary, p.payment_status
        FROM payroll p
        JOIN employees e ON p.employee_id=e.employee_id
        JOIN departments d ON e.department_id=d.department_id
        WHERE p.month=? AND p.year=?
        ORDER BY d.dept_name, e.name
    """, (month, year)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
