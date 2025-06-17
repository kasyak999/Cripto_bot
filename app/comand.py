from pprint import pprint
from sqlalchemy import select, update

from app.config import session, logger
from app.db import sessionDB, Coin
from app.validators import validate_symbol, count_decimal_places


COMMISSION = 0.999  # Комиссия 0.1%
PROCENT = 0.999  # Процент для покупки/продажи


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


def get_coin_price(symbol='BTCUSDT'):
    """Получить цену монеты"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        return
    ticker = ticker['result']['list'][0]
    info = session.get_instruments_info(category="spot", symbol=symbol)
    min_order_usdt = info["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"]
    min_order_coin = info["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]
    logger.info(ticker['symbol'])
    logger.info(f'Рыночная цена: {ticker["lastPrice"]} USDT')
    logger.info(
        f'Минимальный ордер: {min_order_usdt} USDT или '
        f'{min_order_coin} {ticker['symbol']}')

    response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    coin_name = ticker['symbol'].replace("USDT", "")
    balance = next(
        (item for item in response if item["coin"] == coin_name), None)
    if not balance:
        logger.error(f'❌ Монета {coin_name} не найдена в балансе')
        return

    result = sessionDB.execute(
        select(Coin.name).where(Coin.name == symbol)
    ).first()

    if result is None:
        result = sessionDB.add(Coin(
            name=symbol,
            price_buy=ticker["lastPrice"],
            balance=balance['usdValue']
        ))
        sessionDB.commit()
        logger.info('✅ Монета добавлена в базу данных')
    else:
        result = sessionDB.execute(
            update(Coin).where(
                Coin.name == symbol
            ).values(
                price_buy=ticker["lastPrice"],
                balance=balance['usdValue'])
        )
        sessionDB.commit()
        logger.info(
            '🔄 Стоимость и баланс обновлен')


def cycle_coin_price():
    """Проверка цены монеты в цикле"""
    result = sessionDB.execute(select(Coin)).scalars().all()
    for coin in result:
        ticker = validate_symbol(session, coin.name)
        ticker = ticker['result']['list'][0]

        print('')
        print('цена покупки', coin.price_buy)
        print('покупка - 5%', coin.price_buy * PROCENT)
        print('рыночная', ticker["lastPrice"])

        if not float(ticker["lastPrice"]) <= (float(coin.price_buy) * PROCENT):
            continue

        print('Столько всего', coin.balance, 'USD')


def buy_coin(symbol, price):
    """Купить монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        return
    ticker = ticker["result"]["list"][0]
    session.place_order(
        category="spot",
        symbol=symbol,
        side="Buy",
        orderType="Market",
        qty=str(price)
    )
    result_buy = (price * COMMISSION) / float(ticker["lastPrice"])
    logger.info(f"✅ Куплено {result_buy} {ticker['symbol']} на {price} USDT")


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
