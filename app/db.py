from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declared_attr, declarative_base, Session


class PreBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=PreBase)


class Coin(Base):
    price_buy = Column(Float)
    price_sale = Column(Float)
    name = Column(String(200), unique=True)
    balance = Column(Float)
    payback = Column(Integer, default=0)

    def __repr__(self):
        return f'{self.name}'


engine = create_engine('sqlite:///sqlite.db')  # echo=True логи
Base.metadata.create_all(engine)
sessionDB = Session(engine)
