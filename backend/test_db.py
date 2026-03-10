import asyncio
from db.postgres import engine
from sqlalchemy import text

async def test_connection():
    try:
        print("Attempting to connect to the database...")
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
