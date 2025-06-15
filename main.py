import sys
from app.config import args
from app.comand import get_balance


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(
            '⚠️  Не введена ни одна команда.\n'
            'Используйте -h или --help для справки.')
    if args.balance:
        get_balance()
