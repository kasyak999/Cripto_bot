from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
import argparse
from loguru import logger
import sys


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DEMO = os.getenv("DEMO", "false").lower() == "true"

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO")

session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=DEMO
)


class MyArgumentParser(argparse.ArgumentParser):
    """ Ошибка при неправильной команде """
    def error(self, message):
        self.print_help()


parser = MyArgumentParser(description='Биржа')
parser.add_argument(
    '-b',
    '--balance',
    help='Узнать баланс',
    action='store_true',
)

parser.add_argument(
    '-p',
    '--price',
    help='Узнать cтоимость монеты'
)

parser.add_argument(
    '-buy',
    '--buy',
    help='Купить монету'
)

parser.add_argument(
    '-unbuy',
    '--unbuy',
    help='Продать монету'
)

parser.add_argument(
    '-s',
    '--sum',
    type=int,
    help='На сколько USDT продать или купить монету',
)
args = parser.parse_args()
