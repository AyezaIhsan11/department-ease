import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from database import connect_to_mongo
from models.event import Event, EventCategory

async def add_mela_event():
    await connect_to_mongo()
    
    event = Event(
        title="WAHDIYAN MELA",
        description="Cultural festival event.",
        start_date=datetime.fromisoformat("2026-05-06T17:00:00"),
        end_date=datetime.fromisoformat("2026-05-06T22:00:00"),
        category=EventCategory.CULTURAL,
        created_by="admin"
    )
    
    await event.insert()
    print(f"Successfully added event: {event.title}")

if __name__ == "__main__":
    asyncio.run(add_mela_event())
