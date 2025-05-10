from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal, engine
from models import Base, DBUser, DBPartner, DBCity, DBPartnersDiscount
from crud import db_get_discounts

from utls import load_discounts_from_excel, load_discounts_to_database



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
    file_path = 'data/partners_discounts/partners_discounts_bb.xlsx'
    df = load_discounts_from_excel(file_path)
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


# Модели для вывода скидок и партнеров по городу
class DiscountOut(BaseModel):
    id: int
    discription: Optional[str] = None
    corpcard_discount: Optional[str] = None

    class Config:
        orm_mode = True

class PartnerOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    discounts: List[DiscountOut] = []

    class Config:
        orm_mode = True

class CityDiscountsOut(BaseModel):
    id: int
    city_name: str
    partners: List[PartnerOut] = []

    class Config:
        orm_mode = True


@app.get('/cities_discounts', response_model=List[CityDiscountsOut])
def get_cities_discounts(cityname: str = None, db: Session = Depends(get_db)):
    if cityname:
        cities = db.query(DBCity).filter(DBCity.name.ilike("%"+cityname+"%")).all()
        if not cities:
            raise HTTPException(404, detail="Города не найдены")
    else:
        cities = db.query(DBCity).all()
    cities_discounts = []
    for city in cities:
        city_discounts = CityDiscountsOut(id=city.id, city_name=city.name)
        partners = db.query(DBPartner).join(DBPartnersDiscount).filter(DBPartnersDiscount.city_id == city.id).all()
        for partner in partners:
            partner_out = PartnerOut(id=partner.id, name=partner.name, description=partner.description)
            discounts = db.query(DBPartnersDiscount).filter(DBPartnersDiscount.partner_id == partner.id).filter(DBPartnersDiscount.city_id == city.id).all()
            for discount in discounts:
                discount_out = DiscountOut(
                    id=discount.id,
                    discription=discount.discription,
                    corpcard_discount=discount.corpcard_discount
                )
                partner_out.discounts.append(discount_out)
            city_discounts.partners.append(partner_out)
        cities_discounts.append(city_discounts)
    return cities_discounts


@app.get('/cities_discounts/{city_id}', response_model=CityDiscountsOut)
def get_city_discounts(city_id: int, db: Session = Depends(get_db)):
    city = db.query(DBCity).filter(DBCity.id == city_id).first()
    if not city:
        raise HTTPException(404, detail="Город не найден")
    city_discounts = CityDiscountsOut(id=city.id, city_name=city.name)
    partners = db.query(DBPartner).join(DBPartnersDiscount).filter(DBPartnersDiscount.city_id == city.id).all()
    for partner in partners:
        partner_out = PartnerOut(id=partner.id, name=partner.name, description=partner.description)
        discounts = db.query(DBPartnersDiscount).filter(DBPartnersDiscount.partner_id == partner.id).filter(DBPartnersDiscount.city_id == city.id).all()
        for discount in discounts:
            discount_out = DiscountOut(
                id=discount.id,
                discription=discount.discription,
                corpcard_discount=discount.corpcard_discount
            )
            partner_out.discounts.append(discount_out)
        city_discounts.partners.append(partner_out)
    return city_discounts


@app.get('/user_discounts/{user_gab_id}', response_model=CityDiscountsOut)
def get_city_discounts(user_gab_id: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.gab_id == user_gab_id).first()
    if not user.city_id:
        raise HTTPException(404, detail="У пользователя не указан город")
    city = db.query(DBCity).filter(DBCity.id == user.city_id).first()
    if not city:
        raise HTTPException(404, detail="Город не найден")
    city_discounts = CityDiscountsOut(id=city.id, city_name=city.name)
    partners = db.query(DBPartner).join(DBPartnersDiscount).filter(DBPartnersDiscount.city_id == city.id).all()
    for partner in partners:
        partner_out = PartnerOut(id=partner.id, name=partner.name, description=partner.description)
        discounts = db.query(DBPartnersDiscount).filter(DBPartnersDiscount.partner_id == partner.id).filter(DBPartnersDiscount.city_id == city.id).all()
        for discount in discounts:
            discount_out = DiscountOut(
                id=discount.id,
                discription=discount.discription,
                corpcard_discount=discount.corpcard_discount
            )
            partner_out.discounts.append(discount_out)
        city_discounts.partners.append(partner_out)
    return city_discounts


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