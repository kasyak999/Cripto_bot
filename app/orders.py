from app.config import session, logger
from pprint import pprint
from pybit.exceptions import InvalidRequestError, FailedRequestError


def list_orders(symbol=None):
    """ Список ордеров """
    orders = session.get_open_orders(category="spot", symbol=symbol)
    result = []
    for coin in orders['result']['list']:
        # pprint(coin)
        result.append({
            'name': coin['symbol'],
            'orderId': int(coin['orderId']),
            'leavesQty': float(coin['leavesQty']),
            'leavesValue': float(coin['leavesValue']),
            'price': float(coin['price']),
            'side': coin['side']
        })
    pprint(result)
    return result


def delete_coin_order(symbol=None):
    """ Удалить все или один ордер """
    session.cancel_all_orders(
        category="spot",
        symbol=symbol
    )
    if symbol:
        logger.info(f'{symbol} ордера удалены')
    else:
        logger.info('Все ордера удалены')


def add_coin_order(symbol, qty, price):
    """ Создать лимитный ордер """
    try:
        session.place_order(
            category="spot",  # спотовый рынок
            symbol=symbol,  # торговая пара
            side="Buy",  # "Buy" или "Sell"
            orderType="Limit",  # лимитный ордер
            qty=qty,  # количество базовой валюты
            price=price,  # цена лимитного ордера
        )
    except (InvalidRequestError, FailedRequestError) as e:
        logger.error(f'Ошибка API при создании ордера: {str(e)}')
    else:
        logger.info('ордер создан')
