from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
import argparse
from loguru import logger
import sys


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DEMO = True  # True - демо режим / False - не демо

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO")

session = HTTP(
    testnet=False,
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
args = parser.parse_args()
