from pydantic import BaseModel, EmailStr
from datetime import datetime


# Создание нового пользователя (принимаем)
class UserCreate(BaseModel):
    email: EmailStr  # Проверка валидности
    password: str


# Схема ответа с данными пользователя (отдаем)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = (
            True  # позволяет преобразовывать SQLAlchemy модели в Pydantic схемы
        )


class NoteCreate(BaseModel):
    title: str
    content: str | None = None
    tags: list[str]


class NoteOut(BaseModel):
    id: int
    title: str
    content: str | None = None
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut]

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
