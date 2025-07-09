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
    average_price = Column(Float, doc="Средняя цена")
    buy_price = Column(Float, doc="Цена покупки")
    sell_price = Column(Float, doc="Цена продажи")
    count_buy = Column(Integer, default=1, doc="Кол-во покупок")
    stop = Column(Boolean, default=True)

    def __repr__(self):
        return f'{self.name}'


engine = create_engine('sqlite:///db/db.sqlite3')  # echo=True логи
Base.metadata.create_all(engine)
sessionDB = Session(engine)
