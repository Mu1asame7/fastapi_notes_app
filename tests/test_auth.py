import pytest
from httpx import AsyncClient


# Тест успешной регистрации
@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    # 1. Подготавливаем данные
    user_data = {"email": "test@example.com", "password": "secret123"}

    # 2. Отправляем запрос
    response = await client.post("/register", json=user_data)

    # 3. Проверяем результат
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["is_active"] == True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    # Сначала регистрируем пользователя
    user_data = {"email": "duplicate@example.com", "password": "123"}
    await client.post("/register", json=user_data)

    # Пытаемся зарегистрироваться с тем же email
    response = await client.post("/register", json=user_data)

    # Должна быть ошибка 400
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    user_data = {"email": "not-an-email", "password": "123"}
    response = await client.post("/register", json=user_data)

    # FastAPI сам вернёт ошибку 422 при неверных данных
    assert response.status_code == 422
