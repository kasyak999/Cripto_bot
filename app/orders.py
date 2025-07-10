from app.config import logger
from pybit.exceptions import InvalidRequestError, FailedRequestError
from pprint import pprint


def list_orders(session, symbol=None):
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
    # pprint(result)
    return result


def delete_coin_order(session, symbol=None):
    """ Удалить все или один ордер """
    session.cancel_all_orders(
        category="spot",
        symbol=symbol
    )
    if symbol:
        logger.info(f'{symbol} ордера удалены')
    else:
        logger.info('Все ордера удалены')


def add_coin_order(session, symbol, qty, price, side):
    """ Создать лимитный ордер """
    try:
        session.place_order(
            category="spot",  # спотовый рынок
            symbol=symbol,  # торговая пара
            side=side,  # "Buy" или "Sell"
            orderType="Limit",  # лимитный ордер
            qty=qty,  # количество базовой валюты
            price=price,  # цена лимитного ордера
        )
    except (InvalidRequestError, FailedRequestError) as e:
        logger.error(
            f'{symbol}: {side} Ошибка API при создании ордера: {str(e)}')
    else:
        logger.info(f'✅ {symbol}: {side} ордер создан')


def status_coin_order(session, symbol):
    """ Проверка статуса ордера """
    response = session.get_order_history(
        category="spot",
        symbol=symbol,
        limit=2  # последние 2 ордеров
    )
    result = []
    for i in response['result']['list']:
        pprint(i)
        result.append({i['orderId']: i['orderStatus']})
    return result

# Created — ордер создан
# New — новый ордер (ожидает исполнения)
# Filled — полностью исполнен
# PartiallyFilled — частично исполнен
# Cancelled — отменён
# Rejected — отклонён
# PendingCancel — отмена в процессе