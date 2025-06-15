import os
import time
import logging
import matplotlib.pyplot as plt
from pybit.unified_trading import HTTP

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Конфигурация
API_KEY = "Ключи"
API_SECRET = "Ключи"
SYMBOLS = ['PEPEUSDT', 'SHIBUSDT', 'DOGEUSDT', 'FLOKIUSDT', 'BONKUSDT']
MIN_USDT_FOR_REBALANCE = 10  # Минимальная сумма для ребалансировки

class BybitRebalancer:
    def __init__(self, testnet=False):
        self.session = HTTP(
            api_key=API_KEY,
            api_secret=API_SECRET,
            testnet=testnet
        )
        logging.info("Инициализация бота завершена")

    def get_current_balances(self):
        """Получаем текущие балансы всех монет"""
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")
            
            if not response or 'result' not in response or not response['result']['list']:
                logging.error("Неверный формат ответа от API при получении баланса")
                return {}
                
            coins_data = response['result']['list'][0]['coin']
            balances = {}
            
            for coin_data in coins_data:
                coin = coin_data['coin']
                available = coin_data.get('availableToWithdraw', coin_data.get('free', '0'))
                try:
                    balances[coin] = float(available)
                except ValueError:
                    balances[coin] = 0.0
                logging.debug(f"Баланс {coin}: {balances[coin]}")
                    
            return balances
            
        except Exception as e:
            logging.error(f"Ошибка получения балансов: {str(e)}", exc_info=True)
            return {}

    def sell_all_coins(self):
        """Продаем все указанные монеты в USDT"""
        logging.info("=== Начинаем продажу всех монет ===")
        balances = self.get_current_balances()
        
        sold_any = False
        
        for symbol in SYMBOLS:
            coin = symbol.replace('USDT', '')
            if coin in balances and balances[coin] > 0:
                try:
                    logging.info(f"Попытка продажи {balances[coin]} {coin}...")
                    
                    # Получаем информацию о символе
                    symbol_info = self.session.get_instruments_info(
                        category="spot",
                        symbol=symbol
                    )
                    
                    if not symbol_info or 'result' not in symbol_info:
                        logging.error(f"Не удалось получить информацию о символе {symbol}")
                        continue
                        
                    lot_size = float(symbol_info['result']['list'][0]['lotSizeFilter']['qtyStep'])
                    qty = round(balances[coin] / lot_size) * lot_size
                    
                    if qty <= 0:
                        logging.warning(f"Слишком мало {coin} для продажи: {balances[coin]}")
                        continue
                        
                    order = self.session.place_order(
                        category="spot",
                        symbol=symbol,
                        side="Sell",
                        orderType="Market",
                        qty=qty,
                        timeInForce="GTC"
                    )
                    logging.info(f"Успешно продано: {order['result']['orderId']}")
                    sold_any = True
                except Exception as e:
                    logging.error(f"Ошибка при продаже {coin}: {str(e)}", exc_info=True)
            else:
                logging.info(f"Нет позиции по {coin} для продажи")
        
        if not sold_any:
            logging.info("Нечего продавать")
        
        logging.info("=== Продажа завершена ===")
        time.sleep(2)  # Даем время на обработку ордеров

    def get_usdt_balance(self):
        """Получаем текущий баланс USDT"""
        balances = self.get_current_balances()
        usdt_balance = balances.get('USDT', 0.0)
        logging.info(f"Текущий баланс USDT: {usdt_balance:.2f}")
        return usdt_balance

    def get_current_prices(self):
        """Получаем текущие цены"""
        prices = {}
        for symbol in SYMBOLS:
            try:
                ticker = self.session.get_tickers(category="spot", symbol=symbol)
                prices[symbol] = float(ticker['result']['list'][0]['lastPrice'])
                logging.debug(f"Цена {symbol}: {prices[symbol]}")
            except Exception as e:
                logging.error(f"Ошибка получения цены {symbol}: {str(e)}")
                prices[symbol] = 0
        return prices
    
    def get_klines(self, symbol):
        """Получаем исторические данные"""
        try:
            klines = self.session.get_kline(
                category="spot",
                symbol=symbol,
                interval="D",
                limit=2
            )
            return klines['result']['list']
        except Exception as e:
            logging.error(f"Ошибка получения Kline для {symbol}: {str(e)}")
            return None
    
    def calculate_returns(self):
        """Рассчитываем дневную доходность"""
        returns = {}
        for symbol in SYMBOLS:
            klines = self.get_klines(symbol)
            if klines and len(klines) >= 2:
                prev_close = float(klines[0][4])
                current_price = float(klines[1][4])
                returns[symbol] = (current_price - prev_close) / prev_close
                logging.debug(f"Доходность {symbol}: {returns[symbol]*100:.2f}%")
            else:
                returns[symbol] = 0
        return returns
    
    def calculate_weights(self, returns):
        """Рассчитываем новые веса портфеля"""
        sorted_coins = sorted(returns.items(), key=lambda x: x[1])
        weights = {}
        total_rank = sum(i+1 for i in range(len(sorted_coins)))
        
        for i, (coin, ret) in enumerate(sorted_coins):
            weights[coin] = (len(sorted_coins) - i) / total_rank
            logging.debug(f"Вес {coin}: {weights[coin]*100:.2f}%")
        
        return weights

    def place_buy_order(self, symbol, usdt_amount):
        """Размещаем ордер на покупку"""
        try:
            price = float(self.session.get_tickers(
                category="spot",
                symbol=symbol
            )['result']['list'][0]['lastPrice'])
            
            symbol_info = self.session.get_instruments_info(
                category="spot",
                symbol=symbol
            )['result']['list'][0]
            
            lot_size = float(symbol_info['lotSizeFilter']['qtyStep'])
            min_order = float(symbol_info['lotSizeFilter']['minOrderAmt'])
            
            qty = (usdt_amount / price) // lot_size * lot_size
            
            if usdt_amount < min_order:
                logging.warning(f"Сумма {usdt_amount:.2f} USDT меньше минимального ордера {min_order:.2f} для {symbol}")
                return False
                
            if qty <= 0:
                logging.warning(f"Рассчитанное количество {qty} для {symbol} слишком мало")
                return False
                
            order = self.session.place_order(
                category="spot",
                symbol=symbol,
                side="Buy",
                orderType="Market",
                qty=round(qty, 8),
                timeInForce="GTC"
            )
            logging.info(f"Куплено {qty} {symbol} на {usdt_amount:.2f} USDT. Order ID: {order['result']['orderId']}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка при покупке {symbol}: {str(e)}", exc_info=True)
            return False


     def rebalance_portfolio(self):
        """Выполняем ребалансировку портфеля"""
        logging.info("=== Начинаем процесс ребалансировки ===")
        
        # 1. Продаем все монеты
        self.sell_all_coins()
        
        # 2. Получаем текущий баланс USDT
        usdt_balance = self.get_usdt_balance()
        
        if usdt_balance < MIN_USDT_FOR_REBALANCE:
            logging.error(f"Недостаточно USDT для ребалансировки. Требуется: {MIN_USDT_FOR_REBALANCE}, доступно: {usdt_balance:.2f}")
            return
        
        # 3. Рассчитываем доходности и новые веса
        returns = self.calculate_returns()
        weights = self.calculate_weights(returns)
        
        # 4. Покупаем монеты по новым весам
        total_to_invest = usdt_balance * 0.99  # Оставляем 1% на комиссии
        success_count = 0
        
        logging.info("\nНовое распределение:")
        for symbol, weight in weights.items():
            amount = total_to_invest * weight
            if amount > 0:
                logging.info(f"{symbol}: {weight*100:.2f}% (${amount:.2f})")
                if self.place_buy_order(symbol, amount):
                    success_count += 1
        
        # 5. Визуализация
        if success_count > 0:
            self.visualize_distribution(weights)
        
        logging.info("=== Ребалансировка завершена ===")

    def visualize_distribution(self, weights):
        """Визуализация распределения активов"""
        plt.figure(figsize=(12, 6))
        bars = plt.bar(weights.keys(), [w*100 for w in weights.values()])
        
        plt.title('Распределение активов после ребалансировки')
        plt.ylabel('% портфеля')
        plt.xlabel('Монеты')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Добавляем значения на столбцы
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('portfolio_distribution.png')
        logging.info("График распределения сохранен в portfolio_distribution.png")
        plt.show()

if __name__ == "__main__":
    try:
        # Для тестов используйте testnet=True
        bot = BybitRebalancer(testnet=False)
        bot.rebalance_portfolio()
    except Exception as e:
        logging.error(f"Критическая ошибка: {str(e)}", exc_info=True)