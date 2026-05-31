import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import get_connection

# ── Configure your Gmail credentials here ──────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SENDER_EMAIL  = "suchethdsouzas275@gmail.com"   # ← Replace with your Gmail
SENDER_PASS   = "nknv sjpe igmc vopq"          # ← Replace with Gmail App Password
# ──────────────────────────────────────────────────────────────────────────

def send_email(recipient_email, recipient_name, subject, body, sender_name="HR Team"):
    """Send an HTML email. Returns (success: bool, message: str)."""
    # Convert plain-text body — double newlines = paragraphs, single = line breaks
    paragraphs = body.split("\n\n")
    html_paragraphs = "".join(
        f'<p style="margin:0 0 14px;line-height:1.7;font-family:monospace;white-space:pre-wrap;">{para}</p>'
        if "─" in para or "Username" in para or "Password" in para or "Employee ID" in para
        else f'<p style="margin:0 0 14px;line-height:1.7;">{para.replace(chr(10), "<br>")}</p>'
        for para in paragraphs if para.strip()
    )

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;">
      <div style="background:#1a2035;padding:20px 32px;border-radius:8px 8px 0 0;">
        <h2 style="color:#fff;margin:0;font-size:20px;">PayrollPro</h2>
        <p style="color:#8ea0bc;margin:3px 0 0;font-size:12px;">HR Management System</p>
      </div>
      <div style="background:#fff;padding:28px 32px;border:1px solid #e5e7eb;
                  border-top:3px solid #e85d42;border-radius:0 0 8px 8px;">
        <p style="margin:0 0 20px;font-size:15px;">Dear <strong>{recipient_name}</strong>,</p>
        {html_paragraphs}
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
        <p style="color:#888;font-size:12px;margin:0;">
          Regards,<br>
          <strong style="color:#1a2035;">{sender_name}</strong><br>
          <span style="color:#e85d42;">PayrollPro HR System</span>
        </p>
      </div>
    </body></html>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"PayrollPro HR <{SENDER_EMAIL}>"
        msg["To"]      = recipient_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        return True, "Email sent successfully!"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Please check your Gmail App Password in email_service.py."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def log_email(sender, recipient_id, subject, body, status="Sent"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO email_log (sender,recipient_id,subject,body,sent_at,status) VALUES (?,?,?,?,?,?)",
        (sender, recipient_id, subject, body, str(datetime.datetime.now()), status)
    )
    conn.commit()
    conn.close()

def get_email_logs():
    conn = get_connection()
    rows = conn.execute("""
        SELECT el.email_id, el.sender, e.name as recipient_name, e.email as recipient_email,
               el.subject, el.sent_at, el.status
        FROM email_log el
        JOIN employees e ON el.recipient_id = e.employee_id
        ORDER BY el.email_id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
