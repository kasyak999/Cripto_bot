from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

session = HTTP(
    testnet=False,
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True  # Для демо режима установите demo=True
)


# Получить книгу ордеров по бессрочному контракту USDT, BTCUSDT
session.get_orderbook(category="linear", symbol="MNTUSDT")

# # Create five long USDC Options orders.
# # (Currently, only USDC Options support sending orders in bulk.)
# payload = {"category": "option"}
# orders = [{
#   "symbol": "BTC-30JUN23-20000-C",
#   "side": "Buy",
#   "orderType": "Limit",
#   "qty": "0.1",
#   "price": i,
# } for i in [15000, 15500, 16000, 16500, 16600]]

# payload["request"] = orders
# # Submit the orders in bulk.
# session.place_batch_order(payload)


print(session)