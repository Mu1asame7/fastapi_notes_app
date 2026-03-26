from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.models import User, RefreshToken
import secrets

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Хешируем пароль"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка совпадения пароля с хешем"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT настройки
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_token(data: dict) -> str:
    """Создаем JWT токен"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Старая функция для генерации JWT refresh token
# def create_refresh_token(user_id: str) -> str:
#     data = {"sub": str(user_id), "type": "refresh"}
#     expire = datetime.now(timezone.utc) + timedelta(days=7)
#     data.update({"exp": expire})
#     return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# Новая функция для генерации refresh token и хранения в БД
async def create_refresh_token(db: AsyncSession, user_id: int):
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = RefreshToken(
        token=refresh_token, user_id=user_id, expires_at=expires_at
    )

    # Созранение токена в БД
    db.add(new_refresh_token)
    await db.commit()
    await db.refresh(new_refresh_token)

    return new_refresh_token


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
