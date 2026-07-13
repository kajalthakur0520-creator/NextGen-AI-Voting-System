import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# EMAIL CONFIGURATION
# ==========================================
# WARNING: For real email sending, replace these placeholders with real credentials.
# If using Gmail, you MUST generate an "App Password" (do not use your regular password).
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "enter_your_email"
SENDER_PASSWORD = "enter_your_passkey"

def send_otp_email(recipient_email, otp):
    """
    Sends an OTP to the specified email address.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = f"NextGen <{SENDER_EMAIL}>"
        msg["To"] = recipient_email
        msg["Subject"] = "Your NexGen Voting System OTP"

        body = f"Hello,\n\nYour One-Time Password (OTP) for login is: {otp}\n\nDo not share this code with anyone.\n\nBest,\nNexGen Voting Team"
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email OTP: {e}")
        return False
