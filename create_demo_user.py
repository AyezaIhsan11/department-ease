import asyncio
from database import connect_to_mongo, close_mongo_connection
from models.user import User

async def create_demo_user():
    await connect_to_mongo()
    
    # Check if admin already exists
    existing = await User.find_one(User.username == "admin")
    if existing:
        print("Admin user already exists.")
    else:
        hashed_pw = User.hash_password("admin123")
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=hashed_pw,
            role="admin"
        )
        await admin.insert()
        print("Created demo admin user: admin / admin123")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(create_demo_user())
