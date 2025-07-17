from sqlalchemy import Column, Integer, String, Float, Boolean
from app.config import DEMO

from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker)
from sqlalchemy.orm import declarative_base, declared_attr
from contextlib import asynccontextmanager


class PreBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=PreBase)
if not DEMO:
    DB_NAME = 'real-db.sqlite3'
else:
    print('----- Вы в режиме демо счета -----')
    DB_NAME = 'demo-db.sqlite3'
engine = create_async_engine(f'sqlite+aiosqlite:///./db/{DB_NAME}')
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)


@asynccontextmanager
async def get_async_session():
    async with AsyncSessionLocal() as async_session:
        yield async_session


async def init_db():
    """ Создание базы данных и таблиц """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
