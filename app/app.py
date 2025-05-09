from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

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



# Получаем скидки профсоюза, по городу
@app.get('/cc_discounts', response_model=DiscountOut)
def get_discounts(city: str = None, db: Session = Depends(get_db)):
    if not city:
        raise HTTPException(400, "Город не указан")
    discounts = db_get_discounts(db, city)
    if not discounts:
        raise HTTPException(404, "Скидки не найдены")
    return discounts


# Получаем мероприятия, по городу







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