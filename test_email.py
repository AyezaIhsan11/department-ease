import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models.student import Student
from services.email_service import email_service
from config import settings

async def main():
    print("Connecting to DB...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(database=client[settings.DATABASE_NAME], document_models=[Student])
    
    print("Querying students...")
    students = await Student.find(Student.email != None).to_list()
    print(f"Found {len(students)} students.")
    emails = [s.email for s in students if s.email]
    print(f"Emails: {emails}")
    
    if emails:
        print(f"Trying to send test email to first student: {emails[0]}")
        try:
            await email_service.send_email(
                to_emails=[emails[0]],
                subject="Test Email Configuration",
                body="<p>This is a test email to verify SMTP configuration.</p>",
                html=True
            )
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
