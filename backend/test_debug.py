import asyncio
from database import connect_to_mongo, close_mongo_connection
from models.user import User
import traceback

async def main():
    try:
        print("1. Connecting to MongoDB...")
        await connect_to_mongo()
        print("   Connected!")

        print("2. Checking for existing user...")
        # Just check find_one to see if read works
        user = await User.find_one(User.username == "test_debug_admin")
        print(f"   Read query successful. Found: {user}")

        if not user:
            print("3. Attempting to create a user...")
            
            print("   Testing password hashing...")
            hashed_pw = User.hash_password("test_password_123")
            print(f"   Hash generated: {hashed_pw[:10]}...")
            
            new_user = User(
                username="test_debug_admin",
                email="test_debug@example.com",
                password_hash=hashed_pw,
                role="admin"
            )
            await new_user.insert()
            print("   User inserted successfully!")
            
            # Clean up
            await new_user.delete()
            print("   Test user deleted.")
        
    except Exception:
        print("\n!!! ERROR OCCURRED !!!")
        traceback.print_exc()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
