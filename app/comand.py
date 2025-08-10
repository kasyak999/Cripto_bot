import asyncio
import os
import math
from sqlalchemy import select
# from pprint import pprint

from app.config import session, logger
from app.db import get_async_session, Coin
from app.service import balance_coin, get_info_coin
from app.orders import (
    add_coin_order, list_orders, delete_coin_order, status_coin_order)


# Процент снижения для поуцпки -5% (-5% по умолчанию 0.95)
PROCENT_BUY = float(os.getenv('PROCENT_BUY', '0.95'))
# Процент роста для продажи +5% (+5% по умолчанию 1.05)
PROCENT_SELL = float(os.getenv('PROCENT_SELL', '1.05'))


async def get_balance():
    """Получить список монет"""
    response = await asyncio.to_thread(
        session.get_wallet_balance, accountType="UNIFIED")
    # response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    if not response:
        print('💼 В портфеле пока нет монет.')
        return
    result = '💰 Ваш крипто-портфель:\n'

    locked = ''
    for value in response:
        if value['coin'] == 'USDT':
            locked = float(value['walletBalance']) - float(value['locked'])
            locked = (
                f'\n 💵 Всего USDT - {value['walletBalance']}'
                f'\n 💰 Доступно USDT - {locked}')
            continue

        result += (
            f'''
            -------- 🪙  {value['coin']} --------
            🔹 Баланс: {value['walletBalance']}
            💵 Оценка в USD: {value['usdValue']}
            '''
        )
        # pprint(coin)
    print(result + locked)


async def get_add_coin(symbol):
    """Добавить монету"""
    symbol = symbol.upper() + 'USDT'
    ticker = await get_info_coin(symbol)
    if not ticker:
        return

    balance = await balance_coin(symbol)
    if not balance:
        return
    async with get_async_session() as sessionDB:
        result = await sessionDB.execute(
            select(Coin).where(Coin.name == symbol))
        result = result.scalars().first()

        if result is None:
            balance = (
                math.floor(
                    float(
                        balance['walletBalance']) * 10**ticker['base_precision']))
            balance = balance / 10**ticker['base_precision']

            new_coin = Coin(
                name=symbol,
                balance=balance,
            )
            sessionDB.add(new_coin)
            await sessionDB.commit()
            logger.info(f'✅ {symbol} добавлен в базу данных')
        else:
            print(f'{symbol} уже есть в базе данных')


async def list_coins():
    """Получить список монет из базы данных"""
    async with get_async_session() as sessionDB:
        result = await sessionDB.execute(select(Coin))
        result = result.scalars().all()
    if not result:
        print('📦 В базе данных нет ни одной монеты.')
        return
    result_log = '📊 Монеты, сохранённые в базе данных:\n'
    for coin in result:
        average_price = f'{coin.average_price:.8f}' if coin.average_price else None
        buy_price = f'{coin.buy_price:.8f}' if coin.buy_price else None
        sell_price = f'{coin.sell_price:.8f}' if coin.sell_price else None
        buy_order_id = 'остановлено ⛔️' if not coin.buy_order_id else 'в работе 🔄'
        sell_order_id = 'остановлено ⛔️' if not coin.sell_order_id else 'в работе 🔄'
        result_log += f'''
        -------- 🪙  {coin.name} --------
        🆔 id: {coin.id}
        {Coin.__table__.columns.balance.doc}: {coin.balance:.8f}
        {Coin.__table__.columns.purchase_price.doc}: {coin.purchase_price:.8f}
        {Coin.__table__.columns.average_price.doc}: {average_price}
        {Coin.__table__.columns.buy_price.doc}: {buy_price}
        {Coin.__table__.columns.sell_price.doc}: {sell_price}
        {Coin.__table__.columns.buy_order_id.doc}: {buy_order_id}
        {Coin.__table__.columns.sell_order_id.doc}: {sell_order_id}
        '''
    print(result_log)


async def get_delete_coin(id_coin):
    """ Удалить монету из базы данных """
    async with get_async_session() as sessionDB:
        result = await sessionDB.execute(
            select(Coin).where(Coin.id == id_coin)
        )
        result = result.scalars().first()
        if result is None:
            print(
                f"❌ Монеты с id {id_coin}, нет в базе данных")
            return
        await delete_coin_order(session, result.name)
        logger.info(f"{result.name} - монета удалена из базы данных")
        await sessionDB.delete(result)
        await sessionDB.commit()


async def get_update_coin(id_coin, param, sell=False):
    """ Изменить монету в базе данных """
    async with get_async_session() as sessionDB:
        result = await sessionDB.execute(
            select(Coin).where(Coin.id == id_coin))
        result = result.scalars().first()

        balance = await balance_coin(result.name)
        if not balance:
            print('На балансе 0')
            return
        if result is None:
            print(
                f"❌ Монеты с id {id_coin}, нет в базе данных")
            return
        if not param:
            print('Укажите цену: -p 100')
            return

        if result.purchase_price == 0 or sell:
            result.average_price = param
        else:
            result.average_price = (result.purchase_price + param) / 2

        ticker = await get_info_coin(result.name)
        balance = math.floor(
            float(balance['walletBalance']) * 10**ticker['base_precision'])
        balance = balance / 10**ticker['base_precision']
        result.balance = balance
        result.purchase_price = param
        result.buy_price = round(param * PROCENT_BUY, ticker['priceFilter'])
        result.sell_price = round(
            result.average_price * PROCENT_SELL, ticker['priceFilter'])

        print(f'✅ Монета {result.name} успешно обновлена')
        await sessionDB.commit()


async def add_order(id_coin):
    """ Добавление ордеров """
    async with get_async_session() as sessionDB:
        result = await sessionDB.execute(
            select(Coin).where(Coin.id == id_coin))
        result = result.scalars().first()

        if result is None:
            print(
                f"❌ Монеты с id {id_coin}, нет в базе данных")
            return

        await delete_coin_order(session, result.name)
        await add_coin_order(
            session, result.name, result.balance,
            result.sell_price, 'Sell')  # продажа
        await add_coin_order(
            session, result.name, result.balance,
            result.buy_price, 'Buy')  # покупка

        orders = await list_orders(session, result.name)
        buy_order_id = next(
            (i['orderId'] for i in orders if i['side'] == 'Buy'), None)
        sell_order_id = next(
            (i['orderId'] for i in orders if i['side'] == 'Sell'), None)

        result.buy_order_id = buy_order_id if buy_order_id else None
        result.sell_order_id = sell_order_id if sell_order_id else None
        await sessionDB.commit()


async def get_bot_start():
    """Запуск бота"""
    async with get_async_session() as sessionDB:
        result = await sessionDB.execute(
            select(Coin).where(Coin.sell_order_id.is_not(None)))
        result = result.scalars().all()

        for coin in result:
            orders = await status_coin_order(session, coin.name)
            status_buy = next((
                i[str(coin.buy_order_id)] for i in orders
                if str(coin.buy_order_id) in i
            ), None)
            status_sell = next((
                i[str(coin.sell_order_id)] for i in orders
                if str(coin.sell_order_id) in i
            ), None)

            if status_buy == 'Filled':
                logger.info(f'{coin.name}: Ордер на покупку исполнен')
                await get_update_coin(coin.id, coin.buy_price)
                await add_order(coin.id)

            if status_sell == 'Filled':
                logger.info(f'{coin.name}: ордер на продажу исполнен')
                ticker = await get_info_coin(coin.name)
                await get_update_coin(
                    coin.id, float(ticker['lastPrice']), True)
                await add_order(coin.id)
                # await get_delete_coin(coin.id)

            elif status_buy == 'Cancelled':
                logger.info(f'{coin.name}: ордер на покупку отменен')
                coin.buy_order_id = None

            elif status_sell == 'Cancelled':
                logger.info(f'{coin.name}: ордер на продажу отменен')
                coin.sell_order_id = None

        await sessionDB.commit()
