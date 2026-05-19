import asyncio
import sys
import os

# Add backend to path
os.chdir('backend')
sys.path.append(os.getcwd())

from database import connect_to_mongo
from ai.agent import student_agent

async def debug():
    await connect_to_mongo()
    
    print("--- Test 1: Incomplete info ---")
    res1 = await student_agent.process_message("add new student name ayeza")
    print(f"Response: {res1['response']}")
    print(f"Action Taken: {res1['action_taken']}")
    
    print("\n--- Test 2: Complete info ---")
    res2 = await student_agent.process_message(
        "add new student with ID: S123, name: Ayeza Ihsan, email: ayeza@example.com, department: CS, year: 3",
        conversation_id=res1['conversation_id']
    )
    print(f"Response: {res2['response']}")
    print(f"Action Taken: {res2['action_taken']}")

if __name__ == "__main__":
    asyncio.run(debug())
