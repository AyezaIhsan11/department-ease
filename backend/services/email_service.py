import aiosmtplib
import httpx
import base64
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
        
        # 1. Attempt sending via Resend API if API Key is configured
        if settings.RESEND_API_KEY:
            print("RESEND_API_KEY is configured. Attempting to send email via Resend API...")
            
            from_name = settings.SMTP_FROM_NAME or "Department Ease"
            from_email = settings.SMTP_FROM_EMAIL or "onboarding@resend.dev"
            
            # The free tier of Resend requires sending from onboarding@resend.dev unless domain is verified
            resend_from = f"{from_name} <{from_email}>"
            if not from_email or any(provider in from_email for provider in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
                resend_from = f"{from_name} <onboarding@resend.dev>"
                
            payload = {
                "from": resend_from,
                "to": to_emails,
                "subject": subject,
                "html" if html else "text": body
            }
            
            if attachments:
                resend_attachments = []
                for filename, content in attachments:
                    b64_content = base64.b64encode(content).decode("utf-8")
                    resend_attachments.append({
                        "filename": filename,
                        "content": b64_content
                    })
                payload["attachments"] = resend_attachments
                
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        "https://api.resend.com/emails",
                        json=payload,
                        headers=headers
                    )
                    
                    if response.status_code in [200, 201]:
                        print(f"Email sent successfully via Resend to {to_emails}")
                        return
                    else:
                        print(f"Resend API Error: Status {response.status_code}: {response.text}. Falling back to SMTP...")
            except Exception as e:
                print(f"Resend API Exception: {str(e)}. Falling back to SMTP...")

        # 2. Fallback to standard SMTP sending
        # Check if SMTP configuration is provided
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or not settings.SMTP_FROM_EMAIL:
            error_msg = "SMTP configuration is incomplete. Please configure SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL in the environment variables."
            print(error_msg)
            raise ValueError(error_msg)
            
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
        
        # Send email via SMTP
        smtp = None
        try:
            smtp = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=False,
                use_tls=(settings.SMTP_PORT == 465),
                timeout=5.0,
            )
            
            await smtp.connect()
            
            # For port 587, upgrade to TLS via STARTTLS
            if settings.SMTP_PORT == 587:
                await smtp.starttls()
            
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
            print(f"Email sent successfully via SMTP to {to_emails}")
        except Exception as e:
            print(f"SMTP Error: {type(e).__name__}: {e}")
            raise
        finally:
            if smtp:
                try:
                    await smtp.quit()
                except Exception:
                    pass
    
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
