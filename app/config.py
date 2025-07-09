from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
import argparse
from loguru import logger
import sys


load_dotenv()

DEMO = True  # Демо-режим True / Ральный режим False
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
    help='Узнать cтоимость монеты и лимиты'
)
parser.add_argument(
    '-a',
    '--add',
    help='Добавить монету или обновить'
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
    help='Купить монету'
)
parser.add_argument(
    '-unbuy',
    '--unbuy',
    help='Продать монету'
)
parser.add_argument(
    '-u',
    '--usd',
    type=int,
    help='На сколько USDT продать или купить монету',
)

args = parser.parse_args()
