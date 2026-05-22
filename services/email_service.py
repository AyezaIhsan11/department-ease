import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import settings
from typing import List, Optional


class EmailService:
    """Email service for sending notifications"""
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[tuple]] = None
    ):
        """
        Send email
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            html: Whether body is HTML
            attachments: List of (filename, content) tuples
        """
        
        # Check if SMTP configuration is provided
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or not settings.SMTP_FROM_EMAIL:
            print(f"SMTP configuration is incomplete. Bypassing real email send. Logging instead:")
            print(f"To: {to_emails}")
            print(f"Subject: {subject}")
            print(f"Body: {body[:200]}...")
            return
            
        message = MIMEMultipart()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject
        
        # Add body
        if html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
        
        # Add attachments
        if attachments:
            for filename, content in attachments:
                attachment = MIMEApplication(content)
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                message.attach(attachment)
        
        # Send email
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=(settings.SMTP_PORT == 465)
        )
        
        try:
            await smtp.connect()
            if settings.SMTP_PORT == 587 and not smtp.is_connected:
                # This part is handled by connect() usually, but let's be explicit if needed
                pass
            
            if not smtp.use_tls and settings.SMTP_PORT == 587:
                try:
                    await smtp.starttls()
                except aiosmtplib.errors.SMTPException as e:
                    if "already using TLS" not in str(e):
                        raise
            
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
        finally:
            await smtp.quit()
    
    async def send_welcome_email(self, student_email: str, student_name: str):
        """Send welcome email to new student"""
        
        subject = "Welcome to Department Administration System"
        body = f"""
        <h2>Welcome, {student_name}!</h2>
        <p>Your student record has been successfully created in our system.</p>
        <p>If you have any questions, please contact the administration office.</p>
        <br>
        <p>Best regards,<br>Department Administration Team</p>
        """
        
        await self.send_email([student_email], subject, body, html=True)
    
    async def send_report_notification(self, admin_email: str, report_type: str):
        """Send notification when report is generated"""
        
        subject = f"{report_type} Report Generated"
        body = f"""
        <h2>Report Generated</h2>
        <p>Your {report_type} report has been successfully generated.</p>
        <p>Please check the reports section in the admin dashboard.</p>
        """
        
        await self.send_email([admin_email], subject, body, html=True)


# Global instance
email_service = EmailService()
