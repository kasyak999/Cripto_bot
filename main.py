import sys
import time
from datetime import datetime

from app.config import args, logger
from app.comand import (
    get_balance, get_add_coin, buy_coin, sell_coin,
    get_bot_start, get_info_coin, list_coins)
from app.db import sessionDB


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
        # list_coins()
        get_bot_start()
        # try:
        #     while True:
        #         get_bot_start()
        #         print(datetime.now(), 'Бот работает, жду 10 секунд...')
        #         time.sleep(10)
        # except KeyboardInterrupt:
        #     logger.info('Остановка бота...')
        # finally:
        #     sessionDB.close()
        #     logger.info('Бот остановлен.')

    elif args.buy:
        buy_coin(args.buy, args.usd)

    elif args.unbuy:
        sell_coin(args.unbuy, args.usd)
