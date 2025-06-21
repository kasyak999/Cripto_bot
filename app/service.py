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


def get_min_limit(price_usd: int, ticker: dict):
    """ ПРоверка минимального лимита """
    if price_usd < float(ticker['min_usdt']):
        logger.error(
            f'❌ {ticker['symbol']} Процент от покупки '
            f'{price_usd} USDT, меньше минимального лимита '
            f'{ticker["min_usdt"]} USDT'
            '\nНужно добавить монет на баланс')
        return True
    return False
