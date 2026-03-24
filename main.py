from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, AsyncSessionLocal
from models import User, Note
from schemas import UserCreate, UserOut, NoteOut, NoteCreate
from auth import get_password_hash, verify_password, create_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()


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

    access_token = create_token(data={"sub": str(user.id)})
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

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return new_note


@app.get("/notes", response_model=list[NoteOut])
async def read_notes(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Note).where(Note.user_id == current_user.id))
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
    return
