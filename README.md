# PayrollPro

A full-stack Employee Payroll & Attendance Management System built with Flask and SQLite — role-based dashboards for Admin, HR and Employees, with payroll processing, attendance tracking, leave management, performance analytics, and PDF/Excel exports.

**Live demo:** [ems-payrollpro-1.onrender.com](https://ems-payrollpro-1.onrender.com)

> ⚠️ The live demo runs on Render's free tier — the first request after a period of inactivity can take 30–60 seconds to wake up.

---

## Features

- **Role-based access** — separate Admin, HR, and Employee views with permissions enforced per route
- **Multi-tenant architecture** — each registered company gets its own isolated SQLite database, auto-provisioned on signup
- **Employee management** — add, edit, and manage employee records across departments
- **Attendance tracking** — daily marking, bulk mark/apply, department & status filters, monthly summaries, Excel export
- **Payroll engine** — automatic salary calculation with earnings/deductions breakdown, monthly payroll runs, payment processing
- **Leave management** — apply, approve/reject, and track casual-leave balances with history
- **Performance analytics** — ratings across punctuality, task completion, teamwork, communication, and initiative, with trend charts and smart insights
- **Reports & exports** — PDF payslips (ReportLab) and formatted Excel payroll/attendance reports (openpyxl)
- **Announcements** — company-wide or role-targeted announcements board
- **Email integration** — automated credential delivery and notifications via Gmail SMTP
- **Demo mode** — a built-in sandboxed demo account that resets safely without touching real data
- **Responsive UI** — mobile-first navigation (off-canvas drawer), scrollable data tables, and adaptive layouts across every page

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite3 (multi-tenant, per-company `.db` files) |
| Templating | Jinja2 |
| Charts | Chart.js |
| PDF generation | ReportLab |
| Excel generation | openpyxl |
| Plotting (server-side) | Matplotlib, Seaborn |
| Email | Gmail SMTP |
| Deployment | Render (Gunicorn) |

## Screenshots

| Dashboard | Attendance |
|---|---|
| Performance analytics, KPIs, and charts | Daily attendance marking with bulk actions |

| Payroll | Mobile |
|---|---|
| Payroll breakdown & export | Fully responsive on phones and tablets |

*(Add screenshots to a `/screenshots` folder and reference them here, e.g. `![Dashboard](screenshots/dashboard.png)`)*

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/SuchethDsouza/EMS-PayrollPro.git
cd EMS-PayrollPro

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Email features (auto-generated credentials, notifications) use Gmail SMTP. Open `email_service.py` and set your sender address and a [Gmail App Password](https://support.google.com/accounts/answer/185833):

```python
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASS  = "your-16-character-app-password"
```

> For production, move these (and the Flask `secret_key` in `app.py`) into environment variables instead of hardcoding them.

### Run locally

```bash
python app.py
```

The app starts on `http://127.0.0.1:5000`. SQLite databases are created automatically on first run — no manual migration needed.

### Demo accounts

The app seeds a ready-to-use demo tenant on first launch:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `hr` | `hr123` | HR |
| `amit` | `emp123` | Employee |

Demo accounts always run against an isolated sandbox database (`payroll_demo.db`) — changes made here never affect real company data.

## Project Structure

```
EMS-PayrollPro/
├── app.py                  # Flask routes & application logic
├── database.py              # DB setup, multi-tenant provisioning, seeding
├── payroll_engine.py        # Salary calculation logic
├── export_engine.py         # PDF payslip & Excel report generation
├── email_service.py         # Gmail SMTP integration
├── migrate*.py               # One-off schema migration scripts
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/app.js
└── templates/                # Jinja2 templates (25 pages)
    ├── base.html              # Shared layout, sidebar, mobile nav
    ├── dashboard.html, employees.html, attendance.html, payroll.html,
    │   leaves.html, performance.html, announcements.html, reports.html, …
```

## Deployment

This project is deployed on [Render](https://render.com) using Gunicorn as the WSGI server.

**Build command:**
```bash
pip install -r requirements.txt
```

**Start command:**
```bash
gunicorn app:app
```

Push to your connected GitHub branch to trigger an auto-deploy, or use Render's "Manual Deploy" option.

## Roadmap / Ideas

- [ ] Move secrets (SMTP credentials, Flask secret key) to environment variables
- [ ] Migrate from SQLite to PostgreSQL for better concurrent-write support in production
- [ ] Add automated tests
- [ ] Two-factor authentication for admin accounts

## Author

**Sucheth Dsouza**
Department of Computer Applications (MCA), St. Agnes College (Autonomous), Mangaluru
GitHub: [@SuchethDsouza](https://github.com/SuchethDsouza)

## License

This project currently has no license file.