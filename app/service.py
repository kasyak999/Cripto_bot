from app.config import logger
from pybit.exceptions import InvalidRequestError


def validate_symbol(session, symbol):
    """ Проверка символа на корректность """
    try:
        ticker = session.get_tickers(category="spot", symbol=symbol)
        return ticker
    except InvalidRequestError:
        logger.error(
            f"{symbol} - такой монеты нет или она введена не правильно")


def count_decimal_places(value):
    """ Подсчет количества знаков после запятой в числе """
    if '.' in value:
        return len(value.split('.')[-1])
    return 0


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
