import pytest
import pytest_asyncio
import asyncio
import httpx
from httpx import AsyncClient
from sqlalchemy import delete
from main import app
from database import AsyncSessionLocal
from models import User


@pytest_asyncio.fixture(autouse=True)
async def clear_db():
    """Очищает базу данных перед каждым тестом"""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User))
        await session.commit()


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
