import sys
from app.config import args, logger
from app.comand import get_balance, get_price, buy_coin, sell_coin


if __name__ == '__main__':
    if len(sys.argv) == 1:
        logger.error(
            '⚠️  Не введена ни одна команда.\n'
            'Используйте -h или --help для справки.')
    if (args.buy or args.unbuy) and args.sum is None:
        logger.error("--sum обязательно при использовании --unbuy")
        sys.exit(1)

    if args.balance:
        get_balance()
    elif args.price:
        get_price(args.price)
    elif args.buy:
        buy_coin(args.buy, args.sum)
    elif args.unbuy:
        sell_coin(args.unbuy, args.sum)
