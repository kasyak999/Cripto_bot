from pprint import pprint
from sqlalchemy import select, update, delete

from pybit.exceptions import InvalidRequestError

from app.config import session, logger
from app.db import sessionDB, Coin
from app.service import validate_symbol, count_decimal_places, balance_coin


COMMISSION = 0.999  # Комиссия на покупку 0.1% (по умолчанию 0.999)
PROCENT_BUY = 0.9998  # Сумма - 5% (по умолчанию 0.95)
PROCENT_SELL = 1.05  # Сумма + 5% (по умолчанию 1.05)
PROCENT = 0.05  # 5% от суммы (по умолчанию 0.05)


def get_balance():
    """Получить список монет"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    for value in response['result']['list']:
        for coin in value['coin']:
            logger.info(
                f'{coin['coin']} - {coin['walletBalance']}'
                f' / USDT - {coin['usdValue']}'
                # f'{coin['lastPrice']}'
            )
            # pprint(coin)


def get_info_coin(symbol='BTCUSDT'):
    """Узнать cтоимость монеты и лимиты"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        return
    ticker = ticker['result']['list'][0]
    info = session.get_instruments_info(category="spot", symbol=symbol)
    min_order_usdt = info["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"]
    min_order_coin = info["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]
    result = (
        f'--- Информация о {ticker['symbol']}---\n'
        f'Рыночная цена: {ticker["lastPrice"]} USDT\n'
        f'Минимальный ордер: {min_order_usdt} USDT или '
        f'{min_order_coin} {ticker['symbol']}'
    )
    # pprint(ticker)
    return {
        'lastPrice': ticker["lastPrice"],
        'min_usdt': min_order_usdt,
        'min_coin': min_order_coin,
        'info': result
    }


def get_add_coin(symbol='BTCUSDT'):
    """Добавить монету или обновить входную стоимость"""
    ticker = get_info_coin(symbol)
    logger.info(ticker['info'])

    balance = balance_coin(session, symbol)
    if not balance:
        balance = {'usdValue': 0}

    result = sessionDB.execute(
        select(Coin.name).where(Coin.name == symbol)
    ).first()
    if result is None:
        result = sessionDB.add(Coin(
            name=symbol,
            start=ticker["lastPrice"],
            balance=balance['usdValue']
        ))
        sessionDB.commit()
        logger.info('✅ Монета добавлена в базу данных')
    else:
        result = sessionDB.execute(
            update(Coin).where(
                Coin.name == symbol
            ).values(
                start=ticker["lastPrice"],
                balance=balance['usdValue'])
        )
        sessionDB.commit()
        logger.info(
            '🔄 Входная стоимость монеты обновлена')


def get_bot_start():
    """Запуск бота"""
    result = sessionDB.execute(select(Coin)).scalars().all()
    for coin in result:
        if coin.balance == 0:
            logger.error(f'Нет баланса для {coin.name}')
            sessionDB.execute(
                delete(Coin).where(Coin.name == coin.name)
            )
            sessionDB.commit()
            continue

        ticker = get_info_coin(coin.name)

        # ---------------------------
        print('')
        print('цена стартовая', coin.start)
        print('цена покупки', coin.price_buy)
        print('рыночная', ticker["lastPrice"])
        print('Всего в USDT', coin.balance)
        # ---------------------------
        current_price = float(ticker["lastPrice"])
        if coin.price_buy:
            if current_price > (coin.price_buy * PROCENT_BUY):
                # print('не покупать')
                continue
        else:
            if current_price > (coin.start * PROCENT_BUY):
                # print('не покупать 2')
                continue

        buy_coin_usdt = round(coin.balance * PROCENT)
        if buy_coin_usdt < float(ticker["min_usdt"]):
            logger.error('Количество USDT для покупки меньше минимального')
            continue
        logger.info(
            f'Покупаем {coin.name} на {buy_coin_usdt} USDT '
            f'по цене {ticker["lastPrice"]}')
        buy_coin(coin.name, buy_coin_usdt, True)


def buy_coin(symbol, price, action=False):
    """Купить монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        # Проверка символа на корректность
        return

    try:
        session.place_order(
            category="spot",
            symbol=symbol,
            side="Buy",
            orderType="Market",
            qty=str(price)
        )
    except InvalidRequestError as e:
        logger.error(f'Ошибка при покупке монеты: {str(e)}')
    else:
        if not action:
            return

        ticker = ticker["result"]["list"][0]
        balance = balance_coin(session, symbol)
        sessionDB.execute(
            update(Coin).where(
                Coin.name == symbol
            ).values(
                price_buy=ticker["lastPrice"],
                balance=balance['usdValue']))
        sessionDB.commit()

        logger.info(f"✅ Куплено {symbol} на {price * COMMISSION} USDT")


def sell_coin(symbol, price):
    """Продать монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        return
    # Узнаем сколько знаков после запятой можно продать
    info = session.get_instruments_info(category="spot", symbol=symbol)
    rounding = count_decimal_places(
        info["result"]["list"][0]["lotSizeFilter"]['basePrecision'])
    ticker = ticker["result"]["list"][0]
    btc_qty = round(price / float(ticker["lastPrice"]), rounding)
    session.place_order(
        category="spot",
        symbol=symbol,
        side="Sell",
        orderType="Market",
        qty=str(btc_qty)
    )
    logger.info(
        f"✅ Продано {btc_qty * COMMISSION} {ticker['symbol']} на {price} USDT")
