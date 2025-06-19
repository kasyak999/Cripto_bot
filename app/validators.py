from app.config import logger
from pybit.exceptions import InvalidRequestError


def validate_symbol(session, symbol):
    """ Проверка символа на корректность """
    try:
        ticker = session.get_tickers(category="spot", symbol=symbol)
        return ticker
    except InvalidRequestError as e:
        logger.error(f'Ошибка: {e}')
        logger.error(f"Проверь символ {symbol}")


def count_decimal_places(value):
    """ Подсчет количества знаков после запятой в числе """
    if '.' in value:
        return len(value.split('.')[-1])
    return 0


def balance_coin(session, symbol):
    response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    coin_name = symbol.replace("USDT", "")
    balance = next(
        (item for item in response if item["coin"] == coin_name), None)
    return balance
