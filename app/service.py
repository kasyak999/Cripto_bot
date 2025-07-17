from app.config import logger
from pybit.exceptions import InvalidRequestError
import decimal
from pprint import pprint
from app.config import session
import asyncio


async def balance_coin(symbol):
    """Получить баланс монеты"""
    response = await asyncio.to_thread(
        session.get_wallet_balance, accountType="UNIFIED")
    # response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    coin_name = symbol.replace("USDT", "")
    balance = next(
        (item for item in response if item["coin"] == coin_name), None)
    if not balance:
        logger.error(f'Нет баланса для {symbol}')
    return balance


async def get_info_coin(symbol='BTCUSDT'):
    """Узнать cтоимость монеты и лимиты"""
    try:
        ticker = await asyncio.to_thread(
            session.get_tickers, category="spot", symbol=symbol)
        # ticker = session.get_tickers(category="spot", symbol=symbol)
    except InvalidRequestError:
        print(
            f"{symbol} - такой монеты нет или она введена не правильно")
        return

    ticker = ticker['result']['list'][0]
    info = await asyncio.to_thread(
        session.get_instruments_info, category="spot", symbol=symbol)
    # info = session.get_instruments_info(category="spot", symbol=symbol)
    # pprint(info)
    min_order_usdt = info["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"]
    min_order_coin = info["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]
    # Узнаем в каком формате отправлять монету
    base_precision = info["result"]["list"][0]["lotSizeFilter"]["basePrecision"]
    base_precision = abs(decimal.Decimal(
        str(base_precision)).as_tuple().exponent)
    # Узнаем в каком формате отправлять курс
    priceFilter = info["result"]["list"][0]["priceFilter"]['tickSize']
    priceFilter = abs(decimal.Decimal(
        str(priceFilter)).as_tuple().exponent)

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
        ),
        'priceFilter': priceFilter
    }
