from app.config import session, logger
from pprint import pprint
from app.validators import validate_symbol, count_decimal_places


COMMISSION = 0.999  # Комиссия 0.1%


def get_balance():
    """Получить список монет"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    for value in response['result']['list']:
        for coin in value['coin']:
            locked = ''
            if float(coin['locked']) > 0:
                locked = f'(в обороте - {coin['locked']}) '
            logger.info(
                f'{coin['coin']} - {coin['walletBalance']} '
                f'{locked}/ USDT - {coin['usdValue']}'
            )


def get_price(symbol='BTCUSDT'):
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
