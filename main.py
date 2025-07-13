import os
import sys
import time
from datetime import datetime
import requests.exceptions

from app.config import args, logger
from app.comand import (
    get_balance, get_add_coin, get_bot_start, get_info_coin,
    list_coins, get_delete_coin, get_update_coin, add_order)
from app.db import sessionDB
from app.orders import list_orders, delete_coin_order, add_coin_order


TIME_SLEEP = int(os.getenv('TIME_SLEEP', '1')) * 60


def start_bot():
    """ Запуск бота в цикле"""
    while True:
        try:
            get_bot_start()
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'❌ Ошибка при запросе к API: {e}')
        print(f'{datetime.now()}: Бот работает, жду {TIME_SLEEP} секунд...')
        time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        logger.error(
            '⚠️  Не введена ни одна команда.\n'
            'Используйте -h или --help для справки.')

    if args.start:
        logger.info('Запуск бота...')
        try:
            start_bot()
        except KeyboardInterrupt:
            pass
        finally:
            logger.info('Остановка бота...')
            sessionDB.close()
    elif args.balance:
        get_balance()
    elif args.list:
        list_coins()
    elif args.info:
        result = get_info_coin(args.info)
        if result:
            print(result['info'])
    elif args.add:
        get_add_coin(args.add)
    elif args.delete:
        get_delete_coin(args.delete)
    elif args.edit:
        get_update_coin(args.edit, args.price, args.multiply)
    elif args.order:
        add_order(args.order)
