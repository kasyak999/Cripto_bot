import sys
import time
from datetime import datetime
import requests.exceptions

from app.config import args, logger
from app.comand import (
    get_balance, get_add_coin, buy_coin, sell_coin,
    get_bot_start, get_info_coin, list_coins, get_delete_coin)
from app.db import sessionDB


TIME_SLEEP = 1 * 60


def start_bot():
    """ Запуск бота в цикле"""
    while True:
        try:
            if not get_bot_start():
                break
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'❌ Ошибка при запросе к API: {e}')
        print(datetime.now(), f'Бот работает, жду {TIME_SLEEP} секунд...')
        time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        logger.error(
            '⚠️  Не введена ни одна команда.\n'
            'Используйте -h или --help для справки.')
    if (args.buy or args.unbuy) and args.usd is None:
        logger.error(
            "--usd обязательно при использовании --unbuy или --buy")
        sys.exit(1)

    if args.balance:
        get_balance()
    elif args.list:
        list_coins()
    elif args.info:
        result = get_info_coin(args.info)
        if result:
            logger.info(result['info'])
    elif args.add:
        get_add_coin(args.add)
    elif args.start:
        logger.info('Запуск бота...')
        try:
            start_bot()
        except KeyboardInterrupt:
            logger.info('Остановка бота...')
        finally:
            sessionDB.close()
    elif args.buy:
        buy_coin(args.buy, args.usd)
    elif args.unbuy:
        sell_coin(args.unbuy, args.usd)
    elif args.delete:
        get_delete_coin(args.delete)
