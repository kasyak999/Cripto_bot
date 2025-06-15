from app.config import session
from loguru import logger
from pprint import pprint
import sys


logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO")


def get_balance():
    """Получить баланс"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    for value in response['result']['list']:
        for coin in value['coin']:
            # pprint(coin)
            locked = ''
            if float(coin['locked']) > 0:
                locked = f'(в обороте - {coin['locked']}) '
            logger.info(
                f'{coin['coin']} - {coin['walletBalance']} '
                f'{locked}/ USDT - {coin['usdValue']}'
            )
