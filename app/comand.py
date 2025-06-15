from app.config import session, logger
from pprint import pprint


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
            # pprint(coin)
