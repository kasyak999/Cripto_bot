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

parser = argparse.ArgumentParser(description='Биржа')
parser.add_argument(
    '-b',
    '--balance',
    help='Узнать баланс',
    action='store_true',
)
parser.add_argument(
    '-i',
    '--info',
    help='Узнать cтоимость монеты и лимиты'
)
parser.add_argument(
    '-a',
    '--add',
    help='Добавить монету или обновить'
)

parser.add_argument(
    '-c',
    '--cycle',
    help='Проверять стоимость монеты в цикле',
    action='store_true'
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
