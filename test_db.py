import asyncio
from database import engine, Base


async def test_connection():
    async with engine.connect() as conn:
        print("✅ Подключение к БД работает!")
    await engine.dispose()


asyncio.run(test_connection())
