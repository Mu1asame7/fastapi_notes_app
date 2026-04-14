# 📝 Notes API

REST API для управления личными заметками с тегами, полнотекстовым поиском, JWT-аутентификацией и WebSocket-уведомлениями в реальном времени.

## ✨ Особенности

- 🔐 **JWT-аутентификация** с refresh-токенами, хранящимися в базе данных
- 🏷️ **Теги** — связь многие-ко-многим, автоподстановка существующих тегов
- 🔍 **Поиск и фильтрация** — по содержимому, по тегам, сортировка, пагинация
- 📡 **WebSocket** — уведомления о создании, обновлении и удалении заметок
- 🗄️ **Асинхронный SQLAlchemy 2.0** + PostgreSQL
- 📚 **Автоматическая документация** Swagger UI и ReDoc
- 🐳 **Docker** — готовый образ для быстрого развертывания
- 🧪 **Pytest** — тесты основных эндпоинтов

## 🛠️ Стек технологий

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0 (async)
- Alembic
- Pydantic V2
- python-jose (JWT)
- passlib (bcrypt)
- WebSockets
- Docker / Docker Compose
- Pytest

## 🚀 Быстрый старт

### Локальный запуск

```bash
# Клонируем репозиторий
git clone https://github.com/Mu1asame7/fastapi_notes_app.git
cd notes-api

# Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем файл с переменными окружения
cp .env.example .env
# Отредактируйте .env — укажите свои DATABASE_URL и SECRET_KEY

# Запускаем PostgreSQL (если локально)
# Или используйте Docker: docker-compose up -d postgres

# Применяем миграции
alembic upgrade head

# Запускаем сервер
uvicorn app.main:app --reload