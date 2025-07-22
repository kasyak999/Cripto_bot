import os
import sys
import time
from datetime import datetime
import requests.exceptions

from app.config import args, logger
from app.comand import (
    get_balance, get_add_coin, get_bot_start, get_info_coin,
    list_coins, get_delete_coin, get_update_coin, add_order)
from app.db import init_db
import asyncio
# from pprint import pprint


TIME_SLEEP = int(os.getenv('TIME_SLEEP', '1')) * 60


async def start_bot():
    """ Запуск бота в цикле"""
    while True:
        try:
            await get_bot_start()
        except requests.exceptions.ReadTimeout as e:
            logger.error(f'❌ Ошибка при запросе к API: {e}')
        print(f'{datetime.now()}: Бот работает, жду {TIME_SLEEP} секунд...')
        time.sleep(TIME_SLEEP)


async def main():
    await init_db()
    if len(sys.argv) == 1:
        logger.error(
            '⚠️  Не введена ни одна команда.\n'
            'Используйте -h или --help для справки.')

    if args.start:
        logger.info('Запуск бота...')
        await start_bot()
        # try:
        #     await start_bot()
        # except KeyboardInterrupt:
        #     pass
        # finally:
        #     logger.info('Остановка бота...')
        # sessionDB.close()
    elif args.balance:
        await get_balance()
    elif args.list:
        await list_coins()
    elif args.info:
        result = await get_info_coin(args.info)
        if result:
            print(result['info'])
    elif args.add:
        await get_add_coin(args.add)
    elif args.delete:
        await get_delete_coin(args.delete)
    elif args.edit:
        await get_update_coin(args.edit, args.price)
    elif args.order:
        await add_order(args.order)

if __name__ == '__main__':
    asyncio.run(main())
