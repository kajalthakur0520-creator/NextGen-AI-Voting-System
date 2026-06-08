from utils import send_otp_email

# Send a test email to the sender's own email to test
success = send_otp_email("kajalthakur0520@gmail.com", "123456")
if success:
    print("Test email sent successfully!")
else:
    print("Failed to send test email.")
