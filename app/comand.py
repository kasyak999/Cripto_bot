from pprint import pprint
import decimal

from sqlalchemy import select, update, delete

from pybit.exceptions import InvalidRequestError

from app.config import session, logger
from app.db import sessionDB, Coin
from app.service import (
    validate_symbol, balance_coin, get_min_limit)


COMMISSION = 0.999  # Комиссия на покупку 0.1% (по умолчанию 0.999)
PROCENT_BUY = 0.95  # Сумма - 5% (по умолчанию 0.95)
PROCENT_SELL = 1.05  # Сумма + 5% (по умолчанию 1.05)
PROCENT = 0.05  # 5% от суммы (по умолчанию 0.05)


def get_balance():
    """Получить список монет"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    # pprint(response)
    for value in response['result']['list']:
        for coin in value['coin']:
            logger.info(
                f'{coin['coin']} - {coin['walletBalance']}'
                f' / USDT - {coin['usdValue']}'
                # f'{coin['lastPrice']}'
            )
            # pprint(coin)


def list_coins():
    """Получить список монет из базы данных"""
    result = sessionDB.execute(
        select(Coin).where(Coin.stop.is_(False))
    ).scalars().all()
    if not result:
        logger.error('Нет монет в базе данных')
        return
    result_log = 'Монеты в базе данных:\n'
    for coin in result:
        result_log += f'{coin.name} - {coin.balance} USDT\n'
    logger.info(result_log)


def get_info_coin(symbol='BTCUSDT'):
    """Узнать cтоимость монеты и лимиты"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        return
    ticker = ticker['result']['list'][0]
    info = session.get_instruments_info(category="spot", symbol=symbol)
    # pprint(info)
    min_order_usdt = info["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"]
    min_order_coin = info["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]

    base_precision = info["result"]["list"][0]["lotSizeFilter"]["basePrecision"]
    base_precision = abs(decimal.Decimal(
        str(base_precision)).as_tuple().exponent)
    # pprint(ticker)
    return {
        'lastPrice': ticker["lastPrice"],
        'min_usdt': min_order_usdt,
        'min_coin': min_order_coin,
        'base_precision': base_precision,
        'symbol': symbol,
        'info': (
            f'--- Информация о {ticker['symbol']}---\n'
            f'Рыночная цена: {ticker["lastPrice"]} USDT\n'
            f'Минимальный ордер: {min_order_usdt} USDT или '
            f'{min_order_coin} {ticker['symbol']}'
        )
    }


def get_add_coin(symbol='BTCUSDT'):
    """Добавить монету или обновить входную стоимость"""
    ticker = get_info_coin(symbol)
    if not ticker:
        return

    balance = balance_coin(session, symbol)
    if not balance:
        return

    result = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()

    if result is None:
        current_price = float(ticker["lastPrice"])
        price_usd = int(
            (float(balance['walletBalance']) * PROCENT) * current_price)
        if get_min_limit(price_usd, ticker):
            return

        new_coin = Coin(
            name=symbol,
            start=ticker["lastPrice"],
            balance=balance['walletBalance'],
            payback=-abs(
                float(balance['walletBalance']) * float(ticker["lastPrice"]))
        )
        sessionDB.add(new_coin)
        sessionDB.commit()
        logger.info(f'✅ {symbol} добавлен в базу данных')
    else:
        logger.error(f'{symbol} уже есть в базе данных')


def get_bot_start():
    """Запуск бота"""
    result = sessionDB.execute(
        select(Coin).where(Coin.stop.is_(False))).scalars().all()
    if not result:
        logger.error('❌ В базе данных нет активных монет. ')
        return False

    for coin in result:
        ticker = get_info_coin(coin.name)
        current_price = float(ticker["lastPrice"])
        price_usd = int((coin.balance * PROCENT) * current_price)

        if get_min_limit(price_usd, ticker):
            sessionDB.execute(update(Coin).where(
                Coin.name == coin.name).values(stop=True))
            sessionDB.commit()
            continue
        price_coin = round(coin.balance, ticker['base_precision'])
        price_coin = (
            int(price_coin) if ticker['base_precision'] == 0 else price_coin)

        # ---------------------------
        # print('')
        # print('Стартовая', coin.start)
        # print('Цена покупки', coin.price_buy)
        # print('Рыночная', ticker["lastPrice"])
        # print(f'Всего {coin.name} - {coin.balance}')
        # ---------------------------

        if current_price >= (coin.start * PROCENT_SELL):
            logger.info(f'Продаем {coin.name}')
            sell_coin(coin.name, price_coin, True)
        else:
            buy_base = coin.price_buy if coin.price_buy else coin.start
            if current_price <= (buy_base * PROCENT_BUY):
                logger.info(f'Покупаем {coin.name}')
                buy_coin(coin.name, price_usd, True)
    return True


def buy_coin(symbol, price, action=False):
    """Купить монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        # Проверка символа на корректность
        return
    coin = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()
    try:
        session.place_order(
            category="spot",
            symbol=symbol,
            side="Buy",
            orderType="Market",
            qty=str(price)
        )
    except InvalidRequestError as e:
        if "170131" in str(e):
            if action:
                coin.start = True
            logger.error("Недостаточно средств на балансе для покупки.")
        else:
            logger.error(f'Ошибка при покупке монеты: {str(e)}')
    else:
        ticker = ticker["result"]["list"][0]
        logger.info(
            f"✅ Куплено {symbol} на {price * COMMISSION} USDT"
            f' по цене {ticker["lastPrice"]}')
        if not action:
            return
        balance = balance_coin(session, symbol)
        coin.price_buy = ticker["lastPrice"]
        coin.balance = balance['walletBalance']
        coin.payback += -abs(price)
    sessionDB.commit()


def sell_coin(symbol, price, action=False):
    """Продать монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        # Проверка символа на корректность
        return
    coin = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()
    try:
        session.place_order(
            category="spot",
            symbol=symbol,
            side="Sell",
            orderType="Market",
            qty=str(price)
        )
    except InvalidRequestError as e:
        logger.error(f'Ошибка при продаже монеты: {str(e)}')
    else:
        ticker = ticker["result"]["list"][0]
        logger.info(
            f"✅ Продано {price} {symbol}"
            f' по цене {ticker["lastPrice"]}')
        if not action:
            return
        balance = balance_coin(session, symbol)
        coin.balance = balance['walletBalance']
        coin.payback += price * float(ticker["lastPrice"])
        coin.stop = True
    sessionDB.commit()
