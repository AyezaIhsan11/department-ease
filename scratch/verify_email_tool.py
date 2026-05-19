import asyncio
import os
import sys
from dotenv import load_dotenv
from unittest.mock import AsyncMock, patch

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

# Mock services.email_service before importing tools
mock_email_service = AsyncMock()

with patch('services.email_service.email_service', mock_email_service):
    from database import connect_to_mongo
    from ai.tools import send_email_tool
    from models.student import Student

    async def verify_email_tool():
        await connect_to_mongo()
        
        # Get a student ID from the DB
        student = await Student.find_one()
        if not student:
            print("No students found in DB to test with.")
            return
            
        student_id = student.student_id
        recipient_email = student.email
        
        print(f"Testing send_email_tool for student {student_id} ({recipient_email})...")
        
        result = await send_email_tool.ainvoke({
            "student_id": student_id,
            "subject": "Test Subject",
            "body": "Test Body"
        })
        
        print(f"Result: {result}")
        
        # Verify mock call
        mock_email_service.send_email.assert_called_once_with(
            to_emails=[recipient_email],
            subject="Test Subject",
            body="Test Body"
        )
        print("Verification successful: Tool correctly fetched email and called service.")

    if __name__ == "__main__":
        asyncio.run(verify_email_tool())
