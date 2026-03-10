import asyncio
from db.postgres import create_tables

async def init_db():
    print("Creating tables...")
    await create_tables()
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
