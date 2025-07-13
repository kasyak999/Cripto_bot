from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declared_attr, declarative_base, Session


class PreBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=PreBase)


class Coin(Base):
    name = Column(String(200), unique=True, doc="Название монеты")
    balance = Column(Float, doc="Баланс")
    purchase_price = Column(Float, doc="Цена покупки", default=0)
    average_price = Column(Float, doc="Средняя цена")
    buy_price = Column(Float, doc="Ордер на покупку")
    sell_price = Column(Float, doc="Ордер на продажу")
    buy_order_id = Column(Integer, doc="id ордера на покупку")
    sell_order_id = Column(Integer, doc="id ордера на продажу")

    def __repr__(self):
        return f'{self.name}'


engine = create_engine('sqlite:///db/db.sqlite3')  # echo=True логи
Base.metadata.create_all(engine)
sessionDB = Session(engine)
