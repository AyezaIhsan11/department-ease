import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load .env from backend
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from database import connect_to_mongo
from models.student import Student

async def count_students():
    await connect_to_mongo()
    count = await Student.count()
    print(f"Total students: {count}")

if __name__ == "__main__":
    asyncio.run(count_students())
