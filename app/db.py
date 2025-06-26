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
    start = Column(Float)
    price_buy = Column(Float)
    name = Column(String(200))
    balance = Column(Float)
    payback = Column(Float, default=0)
    stop = Column(Boolean, default=True)

    def __repr__(self):
        return f'{self.name}'


engine = create_engine('sqlite:///db/db.sqlite3')  # echo=True логи
Base.metadata.create_all(engine)
sessionDB = Session(engine)
