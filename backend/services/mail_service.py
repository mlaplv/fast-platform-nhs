import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

logger = logging.getLogger("api-gateway")

class MailService:
    """
    Elite V2.2: Centralized Async Mail Service.
    Handles SMTP communication using SSOT environment variables.
    """
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("EMAIL_PORT", "587"))
        self.user = os.getenv("EMAIL_HOST_USER")
        self.password = os.getenv("EMAIL_HOST_PASSWORD")
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        self.default_from = os.getenv("DEFAULT_FROM_EMAIL", self.user)
        self.from_name = os.getenv("EMAILS_FROM_NAME", "Micsmo")

    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body_text: str, 
        body_html: str | None = None
    ) -> bool:
        """
        Sends an email asynchronously via SMTP.
        """
        if not self.user or not self.password:
            logger.error("[MailService] SMTP credentials not configured in .env")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.default_from}>"
        message["To"] = to_email

        # Add plain text part
        message.attach(MIMEText(body_text, "plain"))

        # Add HTML part if provided
        if body_html:
            message.attach(MIMEText(body_html, "html"))

        # SMART TLS LOGIC: Port 465 is implicit SSL, Port 587 is STARTTLS
        # Rule: use_tls=True for 465, use_tls=False for 587
        use_implicit_tls = (self.port == 465)
        
        try:
            # Elite V2.2: Manual connection lifecycle for deep response logging
            smtp = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=use_implicit_tls,
                start_tls=False if use_implicit_tls else True,
                timeout=10
            )
            
            async with smtp:
                await smtp.login(self.user, self.password)
                # Elite V2.2: Capture the actual SMTP response message
                response = await smtp.send_message(message)
                
                # Full logging of SMTP interaction for diagnostic transparency
                status_code = response[0] if isinstance(response, tuple) else "OK"
                log_msg = f"📧 [MailService] Email successfully handed off to {self.host}. Code: {status_code}, Payload: {response}"
                logger.info(log_msg)
                return True

        except Exception as e:
            logger.error(f"❌ [MailService] SMTP Transaction Failed to {to_email}: {str(e)}", exc_info=True)
            return False

mail_service = MailService()
