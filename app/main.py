from fastapi import (
    FastAPI,
    WebSocket,
    HTTPException,
    status,
    Depends,
    Body,
    Query,
    WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db, AsyncSessionLocal
from app.models.models import User, Note, Tag, RefreshToken
from app.schemas.schemas import UserCreate, UserOut, NoteOut, NoteCreate
from app.api.v1.auth import (
    get_password_hash,
    verify_password,
    create_token,
    get_current_user,
    create_refresh_token,
    SECRET_KEY,
    ALGORITHM,
)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from app.services.websocket_manager import ConnectionManager
from jose import jwt, JWTError

app = FastAPI()
Connection = ConnectionManager()


@app.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверка уникален ли email пользователя
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Хешируем пароль
    hashed_password = get_password_hash(user_data.password)

    # Создание пользователя
    new_user = User(
        email=user_data.email, hashed_password=hashed_password, is_active=True
    )

    # Созранение пользователя в БД
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@app.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_token = await create_refresh_token(db, user.id)
    access_token = create_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token.token,
        "token_type": "bearer",
    }


@app.post("/refresh")
async def refresh_token(
    refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)
):
    query = select(RefreshToken).where(
        RefreshToken.token == refresh_token,
        RefreshToken.expires_at > datetime.now(),
        RefreshToken.revoked == False,
    )
    result = await db.execute(query)
    stored_token = result.scalar_one_or_none()
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token(data={"sub": str(stored_token.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/notes", response_model=NoteOut)
async def created_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_note = Note(
        title=note_data.title, content=note_data.content, user_id=current_user.id
    )

    # Добавление тегов
    for tag_name in note_data.tags:
        query = select(Tag).where(Tag.name == tag_name)
        result = await db.execute(query)
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            await db.flush()
        new_note.tags.append(tag)

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note, attribute_names=["tags"])
    # await db.refresh(new_note)

    # Уведомление о создании заметки
    await Connection.send_to_user(
        current_user.id,
        {"type": "note_created", "note_id": new_note.id, "title": note_data.title},
    )

    return new_note


@app.get("/notes", response_model=list[NoteOut])
async def read_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    tags: str | None = None,
    search: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
):
    # Словарь разрешенных полей для сортировки
    allowed_sort_fields = {
        "created_at": Note.created_at,
        "updated_at": Note.updated_at,
        "title": Note.title,
    }
    limit = min(limit, 50)
    queue = (
        select(Note)
        .where(Note.user_id == current_user.id)
        .order_by(Note.created_at.desc())
        .offset(skip)
        .limit(limit)
        .options(selectinload(Note.tags))
    )
    # Поиск по тегам
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        queue = queue.filter(Note.tags.any(Tag.name.in_(tag_list)))

    # Поиск по совпадением в title или content
    if search:
        search_condition = or_(
            Note.title.ilike(f"%{search}%"), Note.content.ilike(f"%{search}%")
        )
        queue = queue.where(search_condition)

    # Сортировка по разрешенному полю
    if sort in allowed_sort_fields:
        sort_column = allowed_sort_fields[sort]
        if order == "desc":
            sort_column = sort_column.desc()
        queue = queue.order_by(sort_column)
    else:
        queue = queue.order_by(Note.created_at.desc())

    result = await db.execute(queue)
    notes = result.scalars().all()
    return notes


@app.get("/notes/{note_id}", response_model=NoteOut)
async def read_notes_number(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Note).where(Note.user_id == current_user.id, Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=404,
            detail="Note not found",
        )
    return note


@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(
    note_data: NoteCreate,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Note).where(Note.user_id == current_user.id, Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=404,
            detail="Note not found",
        )
    note.title = note_data.title
    note.content = note_data.content

    await db.commit()
    await db.refresh(note)

    # Уведомление об изменении
    await Connection.send_to_user(
        current_user.id,
        {"type": "note_updated", "note_id": note_id, "title": note_data.title},
    )

    return note


@app.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Note).where(Note.user_id == current_user.id, Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=404,
            detail="Note not found",
        )

    await db.delete(note)
    await db.commit()

    # Уведомление об удалении
    await Connection.send_to_user(
        current_user.id, {"type": "note_deleted", "note_id": note_id}
    )

    return


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: int, token: str = Query(...)
):
    # token = websocket.query_params.get("token")
    # if not token:
    #     await websocket.close(code=1008)
    #     return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = int(payload.get("sub"))
    except JWTError:
        await websocket.close(code=1008)
        return

    if user_id != token_user_id:
        await websocket.close(code=1008)
        return

    await Connection.connect(websocket, user_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        Connection.disconnect(websocket, user_id)


@app.websocket("/ws/test")
async def test_ws(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("OK")
    await websocket.close()
