from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DEMO = True  # True - демо режим / False - не демо

session = HTTP(
    testnet=False,
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=DEMO  # Для демо режима установите demo=True
)
