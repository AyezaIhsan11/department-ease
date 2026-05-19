import asyncio
import os
import sys

# Add backend to sys.path and change directory to it for .env loading
os.chdir(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.getcwd())

from database import connect_to_mongo
from models.student import Student

async def find_student():
    await connect_to_mongo()
    student = await Student.find_one({
        "$or": [
            {"first_name": {"$regex": "Ayeza", "$options": "i"}},
            {"last_name": {"$regex": "Ihsan", "$options": "i"}}
        ]
    })
    if student:
        print(student.email)
    else:
        print("NOT_FOUND")

if __name__ == "__main__":
    asyncio.run(find_student())
