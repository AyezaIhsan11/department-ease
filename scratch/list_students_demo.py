import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from database import connect_to_mongo
from models.student import Student

async def list_students():
    await connect_to_mongo()
    students = await Student.find_all().to_list()
    for s in students:
        print(f"Name: {s.full_name}, ID: {s.student_id}, Dept: {s.department}")

if __name__ == "__main__":
    asyncio.run(list_students())
