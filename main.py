from app.config import args
from app.comand import get_balance


if __name__ == '__main__':
    if args.balance:
        get_balance()
    else:
        print("-h для получения справки по командам")
