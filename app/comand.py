from pprint import pprint
from sqlalchemy import select, update, delete

from pybit.exceptions import InvalidRequestError

from app.config import session, logger
from app.db import sessionDB, Coin
from app.service import validate_symbol, count_decimal_places, balance_coin


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
        select(Coin)
    ).scalars().all()
    if not result:
        logger.error('Нет монет в базе данных')
        return
    for coin in result:
        logger.info(f'{coin.name} - {coin.balance} USDT ')


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
    if not ticker:
        return

    balance = balance_coin(session, symbol)
    if not balance:
        return

    result = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalar_one_or_none()

    if result is None:
        new_coin = Coin(
            name=symbol,
            start=ticker["lastPrice"],
            balance=balance['walletBalance']
        )
        sessionDB.add(new_coin)
        logger.info(f'✅ {symbol} добавлен в базу данных')
    else:
        result.start = float(ticker["lastPrice"])
        result.balance = balance['walletBalance']
        logger.info(f'🔄 {symbol} обновлен в базе данных')

    sessionDB.commit()


def get_bot_start():
    """Запуск бота"""
    result = sessionDB.execute(select(Coin)).scalars().all()
    for coin in result:
        ticker = get_info_coin(coin.name)
        current_price = float(ticker["lastPrice"])


        # usd_balance = round(coin.balance * PROCENT)
  


        # ---------------------------
        print('')
        print('Стартовая', coin.start)
        print('Цена покупки', coin.price_buy)
        print('Рыночная', ticker["lastPrice"])
        print(f'Всего {coin.name} - {coin.balance}')
        # print('+5%', coin.start * PROCENT_SELL)
        # print('-5%', current_price * PROCENT_BUY)

        # print('price_buy', coin.price_buy)
        # run_c = 106
        # print('Рыночная', run_c)
        # print('+5%', coin.start * PROCENT_SELL)
        # print('start -5%', coin.start * PROCENT_BUY)
        # print('price_buy -5%', coin.price_buy * PROCENT_BUY)
        # current_price = run_c
        # ---------------------------

        if current_price >= (coin.start * PROCENT_SELL):
            logger.info(f'Продаем {coin.name}')
            # sell_coin(coin.name, coin_balance, True)
        else:
            buy_base = coin.price_buy if coin.price_buy else coin.start
            if current_price <= (buy_base * PROCENT_BUY):
                logger.info(f'Покупаем {coin.name}')
                # buy_coin(coin.name, usd_balance, True)


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
        delete_coin = False
        if "170140" in str(e):
            delete_coin = True
            logger.error("Сумма ордера меньше минимального значения.")
        elif "170131" in str(e):
            delete_coin = True
            logger.error("Недостаточно средств на балансе для покупки.")
        else:
            logger.error(f'Ошибка при покупке монеты: {str(e)}')
        if delete_coin:
            sessionDB.execute(
                delete(Coin).where(Coin.name == symbol)
            )
            sessionDB.commit()
    else:
        ticker = ticker["result"]["list"][0]
        logger.info(
            f"✅ Куплено {symbol} на {price * COMMISSION} USDT"
            f' по цене {ticker["lastPrice"]}')
        if not action:
            return
        balance = balance_coin(session, symbol)
        sessionDB.execute(
            update(Coin).where(
                Coin.name == symbol
            ).values(
                price_buy=ticker["lastPrice"],
                balance=balance['usdValue']))
        sessionDB.commit()


def sell_coin(symbol, price, action=False):
    """Продать монету"""
    print('продаем монету', symbol, price)


def sell_coin_false(symbol, price):
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
