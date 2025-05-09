import pandas as pd
from models import DBPartner, DBCity, DBPartnersDiscount


def load_discounts_from_excel(file_path: str) -> pd.DataFrame:
    """
    Загружает данные о скидках из Excel файла и возвращает DataFrame.
    """
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(how='all')  # Удаляем пустые строки
        return df
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return pd.DataFrame()  # Возвращаем пустой DataFrame в случае ошибки
    


def load_discounts_to_database(df: pd.DataFrame, db) -> None:
    """
    Загружает данные о скидках в базу данных.
    """
    for index, row in df.iterrows():
        df_partner = row['Партнер']
        df_city = row['Город']
        df_discription = row['Описание']
        df_corpcard_discount = row['Корп. карта']
        df_rpj_discount = row['РосПрофЖел']

        df_cities = [city.strip() for city in df_city.split(',')]

        # Заполнить партнера в базу данных
        db_partner = db.query(DBPartner).filter(DBPartner.name == df_partner).first()
        if not db_partner:
            db_partner = DBPartner(name=df_partner, description=df_discription)
            db.add(db_partner)
            db.commit()  # Сохраняем изменения в базе данных
            db.refresh(db_partner)  # Обновляем объект партнера, чтобы получить его id

        # Заполнить города в базу данных
        for city in df_cities:
            db_city = db.query(DBCity).filter(DBCity.name == city).first()
            if not db_city:
                db_city = DBCity(name=city)
                db.add(db_city)
                db.commit()
                db.refresh(db_city)

            # Заполнить скидку в базу данных
            db_discount = db.query(DBPartnersDiscount).filter(
                DBPartnersDiscount.partner_id == db_partner.id,
                DBPartnersDiscount.city_id == db_city.id
            ).first()
            if not db_discount:
                db_discount = DBPartnersDiscount(
                    partner_id=db_partner.id,
                    city_id=db_city.id,
                    discription=df_discription,
                    corpcard_discount=df_corpcard_discount,
                    rpj_discount=df_rpj_discount
                )
                db.add(db_discount)
                db.commit()  # Сохраняем изменения в базе данных
                db.refresh(db_discount)
        
    db.close()  # Закрываем соединение с базой данных
    print('Load ended!!!')