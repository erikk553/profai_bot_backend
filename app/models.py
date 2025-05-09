from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Date, 
    Text,
    Float,
    ForeignKey
)
from sqlalchemy.orm import relationship
from database import Base


# Модель пользователя
class DBUser(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gab_id = Column(String, index=True, unique=True)
    city_id = Column(Integer, ForeignKey('cities.id'))

    # city = relationship("DBCity", back_populates="users")


# Модель города
class DBCity(Base):
    __tablename__ = 'cities'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, unique=True)
    region = Column(String, nullable=True, default=None)
    latitude = Column(Float, nullable=True, default=None)
    longitude = Column(Float, nullable=True, default=None)


# Модель партнера профсоюза
class DBPartner(Base):
    __tablename__ = 'partners'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # ipn = Column(String, index=True, unique=True) Если понадобится ИНН
    name = Column(String, index=True, unique=True)
    description = Column(Text, nullable=True, default=None)


# Модель скидки от партнера профсоюза
class DBPartnersDiscount(Base):
    __tablename__ = 'partners_discounts'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    partner_id = Column(Integer, ForeignKey('partners.id'))
    city_id = Column(Integer, ForeignKey('cities.id'))
    discription = Column(Text, nullable=True, default=None)
    corpcard_discount = Column(String, nullable=True, default=None)
    rpj_discount = Column(String, nullable=True, default=None)
    start_date = Column(Date, nullable=True, default=None)
    end_date = Column(Date, nullable=True, default=None)

    # partner = relationship("DBPartner", back_populates="discounts")
    # city = relationship("DBCity", back_populates="discounts")