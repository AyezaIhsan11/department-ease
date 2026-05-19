import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from database import connect_to_mongo
from services.pdf_generator import pdf_generator
from models.student import Student

async def verify_report():
    await connect_to_mongo()
    
    # Check current students
    students = await Student.find_all().to_list()
    print(f"Total students: {len(students)}")
    for s in students:
        print(f"- {s.full_name} enrolled on {s.enrollment_date}")
    
    # Get current year/month
    now = datetime.now()
    year = now.year
    month = now.month
    
    print(f"Generating monthly report for {year}-{month}...")
    pdf_buffer = await pdf_generator.generate_monthly_report(year, month)
    
    output_path = "monthly_report_test.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_buffer.getbuffer())
    
    print(f"Report saved to {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")

if __name__ == "__main__":
    asyncio.run(verify_report())
