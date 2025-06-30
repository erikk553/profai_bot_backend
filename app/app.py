from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal, engine
from app.models import Base, DBUser, DBPartner, DBCity, DBPartnersDiscount
# from crud import db_get_discounts_by_city

from app.utls import load_discounts_from_excel, load_discounts_to_database



Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Подгрузка таблиц excel в БД
@app.on_event("startup")
def startup_event():
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_PATH = BASE_DIR / "data" / "partners_discounts" / "partners_discounts_bb.xlsx"
    df = load_discounts_from_excel(DATA_PATH)
    load_discounts_to_database(df, next(get_db()))



# Работа с партнерами и скидками в БД


class DiscountCreate(BaseModel):
    city_name: str
    discription: Optional[str] = None
    corpcard_discount: Optional[str] = None
    rpj_discount: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class PartnerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    discounts: List[DiscountCreate] = []



@app.post('/partners', response_model=PartnerCreate)
def create_partner(partner: PartnerCreate, db: Session = Depends(get_db)):
    db_partner = DBPartner(name=partner.name, description=partner.description)
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)

    for discount in partner.discounts:
        city = db.query(DBCity).filter(DBCity.name == discount.city_name).first()
        if not city:
            raise HTTPException(404, detail=f"Город {discount.city_name} не найден")
        db_discount = DBPartnersDiscount(
            partner_id=db_partner.id,
            city_id=city.id,
            discription=discount.discription,
            corpcard_discount=discount.corpcard_discount,
            rpj_discount=discount.rpj_discount,
            start_date=discount.start_date,
            end_date=discount.end_date
        )
        db.add(db_discount)

    db.commit()
    db.refresh(db_partner)
    return db_partner


@app.post('/partners/bulk', response_model=List[PartnerCreate])
def create_partners(partners: List[PartnerCreate], db: Session = Depends(get_db)):
    created_partners = []
    for partner in partners:
        db_partner = DBPartner(name=partner.name, description=partner.description)
        db.add(db_partner)
        db.commit()
        db.refresh(db_partner)

        for discount in partner.discounts:
            city = db.query(DBCity).filter(DBCity.name == discount.city_name).first()
            if not city:
                raise HTTPException(404, detail=f"Город {discount.city_name} не найден")
            db_discount = DBPartnersDiscount(
                partner_id=db_partner.id,
                city_id=city.id,
                discription=discount.discription,
                corpcard_discount=discount.corpcard_discount,
                rpj_discount=discount.rpj_discount,
                start_date=discount.start_date,
                end_date=discount.end_date
            )
            db.add(db_discount)

        db.commit()
        created_partners.append(db_partner)

    return created_partners


# Получить все города
class CityOut(BaseModel):
    id: int
    name: str
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        orm_mode = True


@app.get('/cities', response_model=List[CityOut])
def get_cities(db: Session = Depends(get_db)) -> List[CityOut]:
    cities = db.query(DBCity).all()
    return cities

# Работа с пользователем

class UserCreate(BaseModel):
    gab_id: str
    cityname: Optional[str] = None

class UserCityOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    gab_id: str
    city: Optional[UserCityOut] = None

    class Config:
        orm_mode = True


# Получить данные пользователя
@app.get('/user/{gab_id}', response_model=UserOut)
def get_user(gab_id: str, db: Session = Depends(get_db)) -> UserOut:
    user = db.query(DBUser).filter(DBUser.gab_id == gab_id).first()
    if not user:
        raise HTTPException(404, detail="Пользователь не найден")
    return user

# Создать пользователя
@app.post('/user', response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    gab_id, cityname = user.gab_id, user.cityname
    user = db.query(DBUser).filter(DBUser.gab_id == gab_id).first()
    if user:
        raise HTTPException(400, detail="Пользователь уже существует")
    if cityname:
        city = db.query(DBCity).filter(DBCity.name.ilike(cityname)).first()
        if not city:
            city = DBCity(name=cityname)
            db.add(city)
            db.commit()
            db.refresh(city)
    else:
        city = None
    user = DBUser(gab_id=gab_id)
    if city:
        user.city_id = city.id
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Обновить город пользователя
@app.put('/user', response_model=UserOut)
def update_user_city(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    gab_id, cityname = user.gab_id, user.cityname
    user = db.query(DBUser).filter(DBUser.gab_id == gab_id).first()
    if not user:
        raise HTTPException(404, detail="Пользователь не найден")
    city = db.query(DBCity).filter(DBCity.name.ilike(cityname)).first()
    if not city:
        city = DBCity(name=cityname)
        db.add(city)
        db.commit()
        db.refresh(city)
    user.city_id = city.id
    db.commit()
    db.refresh(user)
    return user


# Новые модели для получения скидок по городу и пользователю
class DiscountsUserGet(BaseModel):
    user_gab_id: str

    class Config:
        orm_mode = True

class DiscountOut(BaseModel):
    # discription: Optional[str] = None
    corpcard_discount: Optional[str] = None

    class Config:
        orm_mode = True

class PartnerOut(BaseModel):
    name: str
    description: Optional[str] = None
    discounts: List[DiscountOut] = []

    class Config:
        orm_mode = True

class DiscountCityOut(BaseModel):
    city_name: str
    partners: List[PartnerOut] = []

    class Config:
        orm_mode = True

class UserGabidIn(BaseModel):
    gab_id: str

    class Config:
        orm_mode = True

# Новый эндпоинт для получения скидок по пользователю
@app.get('/discounts_user', response_model=DiscountCityOut)
def get_discounts(user_id: UserGabidIn, db: Session = Depends(get_db)) -> DiscountCityOut:
    user_gab_id = user_id.gab_id
    user = db.query(DBUser).filter(DBUser.gab_id == user_gab_id).first()
    if not user:
        raise HTTPException(404, detail="Пользователь не найден")
    city = user.city
    if not city:
        raise HTTPException(404, detail="У пользователя не указан город")
    # Получаем все скидки по этому городу
    discounts = db.query(DBPartnersDiscount).filter(
        DBPartnersDiscount.city_id == city.id
    ).join(DBPartnersDiscount.partner).all()

    # Группируем скидки по партнёрам
    partners_dict = {}
    for discount in discounts:
        partner = discount.partner
        if partner.id not in partners_dict:
            partners_dict[partner.id] = {
                "name": partner.name,
                "description": partner.description,
                "discounts": []
            }
        partners_dict[partner.id]["discounts"].append({
            "corpcard_discount": discount.corpcard_discount
        })

    # Составляем partners: List[PartnerOut]
    partners_out = [PartnerOut(**data) for data in partners_dict.values()]

    # Возвращаем DiscountCityOut
    return DiscountCityOut(city_name=city.name, partners=partners_out)


class CitynameIn(BaseModel):
    cityname: str

    class Config:
        orm_mode = True

# Новый эндпоинт для получения скидок по городу
@app.get('/discounts_city', response_model=DiscountCityOut)
def get_discounts(city: CitynameIn, db: Session = Depends(get_db)) -> DiscountCityOut:
    city = db.query(DBCity).filter(DBCity.name.ilike(city.cityname)).first()
    if not city:
        raise HTTPException(404, detail="Город не найден")
    # Получаем все скидки по этому городу
    discounts = db.query(DBPartnersDiscount).filter(
        DBPartnersDiscount.city_id == city.id
    ).join(DBPartnersDiscount.partner).all()

    # Группируем скидки по партнёрам
    partners_dict = {}
    for discount in discounts:
        partner = discount.partner
        if partner.id not in partners_dict:
            partners_dict[partner.id] = {
                "name": partner.name,
                "description": partner.description,
                "discounts": []
            }
        partners_dict[partner.id]["discounts"].append({
            "corpcard_discount": discount.corpcard_discount
        })

    # Составляем partners: List[PartnerOut]
    partners_out = [PartnerOut(**data) for data in partners_dict.values()]

    # Возвращаем DiscountCityOut
    return DiscountCityOut(city_name=city.name, partners=partners_out)

# Новый post эндпоинт для получения скидок по городу
@app.post('/discounts_city_post', response_model=DiscountCityOut)
def get_discounts(city: CitynameIn, db: Session = Depends(get_db)) -> DiscountCityOut:
    city = db.query(DBCity).filter(DBCity.name.ilike(city.cityname)).first()
    if not city:
        raise HTTPException(404, detail="Город не найден")
    # Получаем все скидки по этому городу
    discounts = db.query(DBPartnersDiscount).filter(
        DBPartnersDiscount.city_id == city.id,
        DBPartnersDiscount.corpcard_discount.isnot(None),  # Убираем предложения без указанной скидки
        DBPartnersDiscount.corpcard_discount != "NaN"
    ).join(DBPartnersDiscount.partner).all()

    # Группируем скидки по партнёрам
    partners_dict = {}
    for discount in discounts:
        partner = discount.partner
        if partner.id not in partners_dict:
            partners_dict[partner.id] = {
                "name": partner.name,
                "description": partner.description,
                "discounts": []
            }
        partners_dict[partner.id]["discounts"].append({
            "corpcard_discount": discount.corpcard_discount
        })

    # Составляем partners: List[PartnerOut]
    partners_out = [PartnerOut(**data) for data in partners_dict.values()]

    # Возвращаем DiscountCityOut
    return DiscountCityOut(city_name=city.name, partners=partners_out)