import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from database import connect_to_mongo
from ai.tools import request_voucher_tool

async def send_voucher_request():
    await connect_to_mongo()
    
    # Ayeza's ID is S123
    student_id = "S123"
    
    print(f"Sending voucher request to student {student_id}...")
    
    # Call the tool directly (as a tool object, use .ainvoke)
    result = await request_voucher_tool.ainvoke({"student_id": student_id})
    
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(send_voucher_request())
