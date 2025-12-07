# send_email.py
import smtplib
from email.message import EmailMessage
import os

def send_email(to_email, subject, body):
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT") or 465)  # default 465

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg.set_content(body)

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            # smtp.set_debuglevel(1)  # ← debug dimatikan
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)

    except smtplib.SMTPAuthenticationError as auth_err:
        print(f"[ERROR] Autentikasi gagal! Periksa EMAIL_PASSWORD / App Password. Detail: {auth_err}")

    except smtplib.SMTPRecipientsRefused as rj_err:
        print(f"[ERROR] Email ditolak penerima! Detail: {rj_err}")

    except smtplib.SMTPException as smtp_err:
        print(f"[ERROR] SMTP error terjadi: {smtp_err}")

    except Exception as e:
        print(f"[ERROR] Gagal mengirim email ke {to_email}: {e}")
