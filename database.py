from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Строка подключения к базе данных
#    sqlite+aiosqlite:///./test.db  означает:
#    - sqlite - тип БД
#    - aiosqlite - асинхронный драйвер для SQLite
#    - ./test.db - файл базы данных в текущей папке
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 2. Создаем асинхронный движок
#    engine - это "ядро", которое управляет подключениями к БД
#    echo=True - будет выводить все SQL-запросы в консоль (полезно для отладки)
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=True,  # можно убрать после отладки
    future=True  # используем новый стиль SQLAlchemy 2.0
)

# 3. Создаем фабрику сессий
#    SessionLocal - это класс, который создает новые сессии для работы с БД
#    autocommit=False - изменения сохраняются только при commit()
#    autoflush=False - данные не отправляются в БД автоматически
#    bind=engine - привязываем к нашему движку
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 4. Базовый класс для моделей
#    Все наши таблицы будут наследоваться от этого класса
Base = declarative_base()

# 5. Функция-зависимость для получения сессии БД
#    Будет использоваться в FastAPI для каждого запроса
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()