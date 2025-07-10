from app.config import logger
from pybit.exceptions import InvalidRequestError
import decimal
from pprint import pprint


def validate_symbol(session, symbol):
    """ Проверка символа на корректность """
    try:
        ticker = session.get_tickers(category="spot", symbol=symbol)
        return ticker
    except InvalidRequestError:
        print(
            f"{symbol} - такой монеты нет или она введена не правильно")


def balance_coin(session, symbol):
    """Получить баланс монеты"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    coin_name = symbol.replace("USDT", "")
    balance = next(
        (item for item in response if item["coin"] == coin_name), None)
    if not balance:
        logger.error(f'Нет баланса для {symbol}')
    return balance


def get_info_coin(session, symbol='BTCUSDT'):
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
