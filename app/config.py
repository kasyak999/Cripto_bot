from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
import argparse
from loguru import logger
import sys


load_dotenv()

DEMO = True if os.getenv('DEMO') == 'true' else False
API_KEY = os.getenv('DEMO_API_KEY') if DEMO else os.getenv('API_KEY')
API_SECRET = os.getenv('DEMO_API_SECRET') if DEMO else os.getenv('API_SECRET')

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO")
logger.add(
    "log.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)

session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=DEMO
)

parser = argparse.ArgumentParser(description='Биржа')
parser.add_argument(
    '-b',
    '--balance',
    help='Узнать баланс всех монет',
    action='store_true',
)
parser.add_argument(
    '-ls',
    '--list',
    help='Список монет в базе данных',
    action='store_true',
)
parser.add_argument(
    '-i',
    '--info',
    help='Узнать cтоимость монеты и лимиты. Пример: -info BTCUSDT'
)
parser.add_argument(
    '-a',
    '--add',
    help='Добавить монету в базу данных. Пример: -add BTCUSDT'
)
parser.add_argument(
    '-d',
    '--delete',
    help='Удалить монету из базы данных. Пример: -delete BTCUSDT'
)

parser.add_argument(
    '-s',
    '--start',
    help='Запуск бота',
    action='store_true'
)

parser.add_argument(
    '-buy',
    '--buy',
    help='Купить монету. Пример: -buy BTCUSDT -u 100'
)
parser.add_argument(
    '-unbuy',
    '--unbuy',
    help='Продать монету. Пример: -unbuy BTCUSDT -u 100'
)
parser.add_argument(
    '-u',
    '--usd',
    type=int,
    help='На сколько USDT продать или купить монету',
)

parser.add_argument(
    '-e',
    '--edit',
    help='Изменить монету. Пример: -edit BTCUSDT -p help'
)

parser.add_argument(
    '-p',
    '--param',
    nargs='+',
    metavar='KEY=VALUE',
    help='Параметры',
)

args = parser.parse_args()
