import asyncio
from db.postgres import get_db, AsyncSessionLocal
from services.auth_service import register_user
from schemas.schemas import RegisterRequest

async def test_register():
    try:
        req = RegisterRequest(
            name="Debug User",
            email="debug@example.com",
            password="password123",
            age=25,
            monthly_income=5000,
            monthly_expenses=2000,
            primary_goal="Wealth"
        )
        async with AsyncSessionLocal() as db:
            result = await register_user(db, req)
            print("SUCCESS:", result)
            await db.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_register())
