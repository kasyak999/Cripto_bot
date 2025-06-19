import sys
from app.config import args, logger
from app.comand import (
    get_balance, get_add_coin, buy_coin, sell_coin,
    get_bot_start, get_info_coin)


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
    elif args.info:
        result = get_info_coin(args.info)
        logger.info(result['info'])
    elif args.add:
        get_add_coin(args.add)
    elif args.start:
        get_bot_start()

    elif args.buy:
        buy_coin(args.buy, args.usd)
    elif args.unbuy:
        sell_coin(args.unbuy, args.usd)
