from pydantic import BaseModel
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Base
# from crud import db_get_user, db_create_user


Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic-модель Пользователь для создания и получения данных
class UserInOut(BaseModel):
    gab_id: str
    city: Optional[str] = None


# Создание пользователя или получение его данных 
@app.get('users/{user_gab_id}', UserInOut)
def get_create_user(user_gab_id: str, db: Session = Depends(get_db)):
    user = db_get_user(db, user_gab_id)
    if not user:
        user = db_create_user(db, user_gab_id)
    if not user:
        HTTPException(500, "Не удалось создать пользователя")
    return user

# Добавляем пользователю город
@app.patch('users/{user_gab_id}', UserInOut)
def update_user(user_gab_id: str, db: Session = Depends(get_db)):
    # todo: create func
    pass 


# Получаем скидки профсоюза, по городу

# Получаем мероприятия, по городу