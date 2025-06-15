from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
import argparse


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DEMO = True  # True - демо режим / False - не демо

session = HTTP(
    testnet=False,
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
args = parser.parse_args()
