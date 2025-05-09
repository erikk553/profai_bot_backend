from datetime import date

from models import DBUser, DBCity, DBPartner, DBPartnersDiscount
from sqlalchemy.orm import Session
from typing import List, Optional



def get_discounts(db: Session, city: str) -> List[DBPartnersDiscount]:
    """
    Получаем скидки по городу
    """
    city = db.query(DBCity).filter(DBCity.name == city).first()
    if not city:
        return []
    return db.query(DBPartnersDiscount).filter(DBPartnersDiscount.city_id == city.id).all()



def db_get_discounts(db: Session, city: str) -> List[DBPartnersDiscount]:
    """
    Получаем скидки по городу
    """
    city = db.query(DBCity).filter(DBCity.name == city).first()
    if not city:
        return []
    return db.query(DBPartnersDiscount).filter(DBPartnersDiscount.city_id == city.id).all()


# def db_get_user(db: Session, gab_id: str) -> Optional[Employee]:
#     """
#     Получаем пользователя по его gab_id
#     """
#     return db.query(Employee).filter(Employee.gab_id == gab_id).first()


# def db_create_user(db: Session, gab_id: str) -> Optional[Employee]:
#     """
#     Создаем пользователя по его gab_id
#     """
#     db_user = Employee(gab_id=gab_id)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user