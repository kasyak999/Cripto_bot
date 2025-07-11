import os
import math
from pprint import pprint
from sqlalchemy import select, update
import time
from app.config import session, logger
from app.db import sessionDB, Coin
from app.service import balance_coin, get_info_coin
from app.orders import (
    add_coin_order, list_orders, delete_coin_order, status_coin_order)


# Процент снижения для поуцпки -5% (-5% по умолчанию 0.95)
PROCENT_BUY = float(os.getenv('PROCENT_BUY', '0.95'))
# Процент роста для продажи +5% (+5% по умолчанию 1.05)
PROCENT_SELL = float(os.getenv('PROCENT_SELL', '1.05'))
# USDT на которую будет покупаться монета
BUY_USDT = float(os.getenv('BUY_USDT', '5.1'))
# Комиссия на покупку 0.1800% (по умолчанию 0.9982)
COMMISSION = float(os.getenv('COMMISSION', '0.9982'))


def get_balance():
    """Получить список монет"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    if not response:
        print('💼 В портфеле пока нет монет.')
        return
    result = '💰 Ваш крипто-портфель:\n'
    for value in response:
        result += (
            f'''
            -------- 🪙  {value['coin']} --------
            🔹 Баланс: {value['walletBalance']}
            💵 Оценка в USD: {value['usdValue']}
            '''
        )
        # pprint(coin)
    print(result)


def get_add_coin(symbol):
    """Добавить монету"""
    symbol = symbol.upper() + 'USDT'
    ticker = get_info_coin(session, symbol)
    if not ticker:
        return

    balance = balance_coin(session, symbol)
    if not balance:
        return

    result = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()

    if result is None:
        balance = (
            math.floor(
                float(balance['walletBalance']) * 10**ticker['base_precision']))
        balance = balance / 10**ticker['base_precision']

        new_coin = Coin(
            name=symbol,
            balance=balance,
        )
        sessionDB.add(new_coin)
        sessionDB.commit()
        logger.info(f'✅ {symbol} добавлен в базу данных')
    else:
        print(f'{symbol} уже есть в базе данных')


def list_coins():
    """Получить список монет из базы данных"""
    result = sessionDB.execute(
        select(Coin)).scalars().all()
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
        {Coin.__table__.columns.average_price.doc}: {average_price}
        {Coin.__table__.columns.buy_price.doc}: {buy_price}
        {Coin.__table__.columns.sell_price.doc}: {sell_price}
        {Coin.__table__.columns.count_buy.doc}: {coin.count_buy}
        {Coin.__table__.columns.buy_order_id.doc}: {buy_order_id}
        {Coin.__table__.columns.sell_order_id.doc}: {sell_order_id}
        '''
    print(result_log)


def get_delete_coin(id_coin):
    """ Удалить монету из базы данных """
    result = sessionDB.execute(
        select(Coin).where(Coin.id == id_coin)
    ).scalars().first()
    if result is None:
        print(
            f"❌ Монеты с id {id_coin}, нет в базе данных")
        return
    delete_coin_order(session, result.name)
    logger.info(f"{result.name} - монета удалена из базы данных")
    sessionDB.delete(result)
    sessionDB.commit()


def get_update_coin(id_coin, param):
    """ Изменить монету в базе данных """
    result = sessionDB.execute(
        select(Coin).where(Coin.id == id_coin)
    ).scalars().first()
    if result is None:
        print(
            f"❌ Монеты с id {id_coin}, нет в базе данных")
        return
    if param:
        ticker = get_info_coin(session, result.name)
        result.average_price = param
        result.buy_price = round(param * PROCENT_BUY, ticker['priceFilter'])
        result.sell_price = round(param * PROCENT_SELL, ticker['priceFilter'])
    else:
        print('Укажите цену: -p 100')
        return
    sessionDB.commit()
    print(f'✅ Монета {result.name} успешно обновлена')


def add_order(id_coin):
    """ Добавление ордеров """
    result = sessionDB.execute(
        select(Coin).where(Coin.id == id_coin)
    ).scalars().first()

    if result is None:
        print(
            f"❌ Монеты с id {id_coin}, нет в базе данных")
        return
    delete_coin_order(session, result.name)
    ticker = get_info_coin(session, result.name)

    add_coin_order(
        session, result.name, result.balance,
        result.sell_price, 'Sell')  # продажа

    qty_buy = round(
        (BUY_USDT * result.count_buy) / result.buy_price,
        ticker['base_precision'])
    add_coin_order(
        session, result.name, qty_buy,
        result.buy_price, 'Buy')  # покупка

    orders = list_orders(session, result.name)
    buy_order_id = next(
        (i['orderId'] for i in orders if i['side'] == 'Buy'), None)
    sell_order_id = next(
        (i['orderId'] for i in orders if i['side'] == 'Sell'), None)

    result.buy_order_id = buy_order_id if buy_order_id else None
    result.sell_order_id = sell_order_id if sell_order_id else None
    sessionDB.commit()


def get_bot_start():
    """Запуск бота"""
    result = sessionDB.execute(
        select(Coin).where(Coin.sell_order_id.is_not(None))
    ).scalars().all()

    for coin in result:
        orders = status_coin_order(session, coin.name)
        status_buy = next((
            i[str(coin.buy_order_id)] for i in orders
            if str(coin.buy_order_id) in i
        ), None)
        status_sell = next((
            i[str(coin.sell_order_id)] for i in orders
            if str(coin.sell_order_id) in i
        ), None)

        if status_buy == 'Filled':
            print('ордер исполнен')
        if status_sell == 'Filled':
            print('ордер исполнен')
        time.sleep(1)

        print(coin.name)
        print(status_sell)
        print(status_buy)
        print()



# def get_bot_start():
#     """Запуск бота"""
#     result = sessionDB.execute(
#         select(Coin).where(Coin.stop.is_(False))).scalars().all()

#     for coin in result:
#         ticker = get_info_coin(coin.name)
#         if get_min_limit(BUY_USDT, ticker):
#             sessionDB.execute(update(Coin).where(
#                 Coin.name == coin.name).values(stop=True))
#             sessionDB.commit()
#             continue

#         if float(ticker["lastPrice"]) >= (coin.start * PROCENT_SELL):
#             logger.info(f'Продаем {coin.name}')
#             price_coin = round(coin.balance, ticker['base_precision'])
#             price_coin = (
#                 math.floor(coin.balance * 10**ticker['base_precision']))
#             price_coin = price_coin / 10**ticker['base_precision']
#             if ticker['base_precision'] == 0:
#                 price_coin = int(price_coin)
#             sell_coin(coin.name, price_coin)
#         else:
#             price_buy = coin.price_buy if coin.price_buy else coin.start
#             if float(ticker["lastPrice"]) <= (price_buy * PROCENT_BUY):
#                 logger.info(f'Покупаем {coin.name}')
#                 buy_coin(coin.name, BUY_USDT)


# def buy_coin(symbol, price):
#     """Купить монету"""
#     ticker = validate_symbol(session, symbol)
#     if not ticker:
#         # Проверка символа на корректность
#         return
#     result = sessionDB.execute(
#         select(Coin).where(Coin.name == symbol)
#     ).scalars().first()
#     try:
#         session.place_order(
#             category="spot",
#             symbol=symbol,
#             side="Buy",
#             orderType="Market",
#             qty=str(price)
#         )
#     except InvalidRequestError as e:
#         if "170131" in str(e):
#             result.start = True
#             logger.error("Недостаточно средств на балансе для покупки.")
#         else:
#             logger.error(f'Ошибка при покупке монеты: {str(e)}')
#     else:
#         ticker = ticker["result"]["list"][0]
#         logger.info(
#             f"✅ Куплено {symbol} на {price * COMMISSION} USDT"
#             f' по цене {ticker["lastPrice"]}')
#         balance = balance_coin(session, symbol)
#         result.price_buy = ticker["lastPrice"]
#         result.balance = balance['walletBalance']
#         result.payback -= price
#     sessionDB.commit()


# def sell_coin(symbol, price):
#     """Продать монету"""
#     ticker = validate_symbol(session, symbol)
#     if not ticker:
#         # Проверка символа на корректность
#         return
#     result = sessionDB.execute(
#         select(Coin).where(Coin.name == symbol)
#     ).scalars().first()
#     try:
#         session.place_order(
#             category="spot",
#             symbol=symbol,
#             side="Sell",
#             orderType="Market",
#             qty=str(price)
#         )
#     except InvalidRequestError as e:
#         logger.error(f'Ошибка при продаже монеты: {str(e)}')
#     else:
#         ticker = ticker["result"]["list"][0]
#         logger.info(
#             f"✅ Продано {price} {symbol}"
#             f' по цене {ticker["lastPrice"]}')
#         balance = balance_coin(session, symbol)
#         result.balance = balance['walletBalance']
#         result.payback += price * float(ticker["lastPrice"])
#         result.stop = True
#     sessionDB.commit()
