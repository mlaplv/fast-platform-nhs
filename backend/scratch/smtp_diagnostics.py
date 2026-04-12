import asyncio
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def test_smtp():
    host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.getenv("EMAIL_PORT", "465"))
    user = os.getenv("EMAIL_HOST_USER")
    password = os.getenv("EMAIL_HOST_PASSWORD")
    from_email = os.getenv("DEFAULT_FROM_EMAIL", user)
    
    print(f"Connecting to {host}:{port} as {user}...")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "SMTP Diagnostic Test - SmartShop"
    message["From"] = f"Diagnostic <{from_email}>"
    message["To"] = "vinasky.vn@gmail.com"
    message.attach(MIMEText("This is a diagnostic test.", "plain"))
    
    try:
        smtp = aiosmtplib.SMTP(
            hostname=host,
            port=port,
            use_tls=(port == 465),
            start_tls=(port == 587)
        )
        await smtp.connect()
        print("Connected.")
        
        await smtp.login(user, password)
        print("Logged in.")
        
        response = await smtp.send_message(message)
        print(f"Message sent! Response: {response}")
        
        await smtp.quit()
        print("Finished.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_smtp())
