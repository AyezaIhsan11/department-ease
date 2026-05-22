from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import settings
from models.student import Student
from models.user import User
from models.event import Event
from models.chat_history import ChatHistory
from models.voucher import Voucher


# Global database client
db_client: AsyncIOMotorClient = None
db_initialized = False


async def connect_to_mongo():
    """Connect to MongoDB and initialize Beanie ODM"""
    global db_client, db_initialized
    
    if db_initialized:
        return
        
    db_client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    await init_beanie(
        database=db_client[settings.DATABASE_NAME],
        document_models=[
            Student,
            User,
            Event,
            ChatHistory,
            Voucher
        ]
    )
    
    db_initialized = True
    print(f"Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global db_client
    
    if db_client:
        db_client.close()
        print("MongoDB connection closed")
