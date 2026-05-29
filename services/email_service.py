import httpx
import aiosmtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import settings
from typing import List, Optional


class EmailService:
    """Email service — uses Resend API when RESEND_API_KEY is set,
    falls back to SMTP (aiosmtplib) otherwise."""

    # ------------------------------------------------------------------ #
    #  Resend API                                                          #
    # ------------------------------------------------------------------ #

    async def _send_via_resend(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[tuple]] = None,
    ):
        """Send email through the Resend HTTP API."""

        from_address = (
            f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            if settings.SMTP_FROM_EMAIL
            else "Department Ease <onboarding@resend.dev>"
        )

        payload = {
            "from": from_address,
            "to": to_emails,
            "subject": subject,
        }

        if html:
            payload["html"] = body
        else:
            payload["text"] = body

        if attachments:
            payload["attachments"] = [
                {
                    "filename": filename,
                    "content": base64.b64encode(content).decode("utf-8"),
                }
                for filename, content in attachments
            ]

        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
            )

        if response.status_code not in (200, 201):
            error_detail = response.text
            print(f"Resend API error {response.status_code}: {error_detail}")
            raise RuntimeError(
                f"Resend API returned {response.status_code}: {error_detail}"
            )

        print(f"Email sent via Resend to: {', '.join(to_emails)}")
        return response.json()

    # ------------------------------------------------------------------ #
    #  SMTP fallback                                                       #
    # ------------------------------------------------------------------ #

    async def _send_via_smtp(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[tuple]] = None,
    ):
        """Send email using aiosmtplib (SMTP fallback)."""

        missing = [
            k for k, v in {
                "SMTP_HOST": settings.SMTP_HOST,
                "SMTP_USERNAME": settings.SMTP_USERNAME,
                "SMTP_PASSWORD": settings.SMTP_PASSWORD,
                "SMTP_FROM_EMAIL": settings.SMTP_FROM_EMAIL,
            }.items() if not v
        ]
        if missing:
            raise ValueError(
                f"SMTP configuration is incomplete. Missing: {', '.join(missing)}"
            )

        message = MIMEMultipart()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject

        if html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))

        if attachments:
            for filename, content in attachments:
                part = MIMEApplication(content)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(part)

        port = settings.SMTP_PORT or 587

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=port,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            use_tls=(port == 465),
            start_tls=(port == 587),
        )
        print(f"Email sent via SMTP to: {', '.join(to_emails)}")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[tuple]] = None,
    ):
        """
        Send an email.  Prefers Resend API when RESEND_API_KEY is configured,
        otherwise falls back to SMTP.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Email body (plain text or HTML)
            html: Set True if body is HTML
            attachments: List of (filename, bytes) tuples
        """
        if settings.RESEND_API_KEY:
            await self._send_via_resend(
                to_emails=to_emails,
                subject=subject,
                body=body,
                html=html,
                attachments=attachments,
            )
        else:
            await self._send_via_smtp(
                to_emails=to_emails,
                subject=subject,
                body=body,
                html=html,
                attachments=attachments,
            )

    async def send_welcome_email(self, student_email: str, student_name: str):
        """Send welcome email to a newly created student."""

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
        """Send notification when a report is generated."""

        subject = f"{report_type} Report Generated"
        body = f"""
        <h2>Report Generated</h2>
        <p>Your {report_type} report has been successfully generated.</p>
        <p>Please check the reports section in the admin dashboard.</p>
        """
        await self.send_email([admin_email], subject, body, html=True)


# Global instance
email_service = EmailService()
