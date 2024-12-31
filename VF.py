import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(recipient_email, CODE):
    re = recipient_email

    send_email_segment = ""
    sender_password = ""
    subject = "VERIFICATION CODE"
    body = "Your code - " + CODE

    se = send_email_segment
    sp = sender_password

    msg = MIMEMultipart()
    msg['From'] = se
    msg['To'] = re
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(se, sp)
        text = msg.as_string()
        server.sendmail(se, re, text)
        server.quit()
        print("Письмо успешно отправлено")
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")
