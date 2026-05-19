import asyncio
import os
import sys

# Add backend to sys.path and change directory to it for .env loading
os.chdir(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.getcwd())

from services.email_service import email_service
from config import settings

async def test_smtp():
    print("Starting SMTP connection test...")
    print(f"Host: {settings.SMTP_HOST}")
    print(f"Port: {settings.SMTP_PORT}")
    print(f"User: {settings.SMTP_USERNAME}")
    print(f"From: {settings.SMTP_FROM_EMAIL}")
    
    if settings.SMTP_USERNAME == "your-email@example.com":
        print("\nWARNING: You are still using the placeholder email address.")
        print("Please update backend/.env with your real SMTP credentials.")
        return

    recipient = input("\nEnter a recipient email address to send a test message: ")
    
    try:
        print(f"\nAttempting to send test email to {recipient}...")
        await email_service.send_email(
            to_emails=[recipient],
            subject="SMTP Connection Test - Department Ease",
            body="If you are reading this, your SMTP configuration for Department Ease is working correctly!"
        )
        print("\nSUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"\nFAILED: Could not send email.")
        print(f"Error: {str(e)}")
        print("\nCommon issues:")
        print("1. Incorrect credentials.")
        print("2. Using Gmail? You need an 'App Password'.")
        print("3. Firewall or ISP blocking port 587.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If run non-interactively, use first arg as recipient
        recipient = sys.argv[1]
        asyncio.run(email_service.send_email(
            to_emails=[recipient],
            subject="SMTP Connection Test - Department Ease",
            body="If you are reading this, your SMTP configuration for Department Ease is working correctly!"
        ))
    else:
        asyncio.run(test_smtp())
