import os
import decimal
import math
from pprint import pprint
from sqlalchemy import select, update
from pybit.exceptions import InvalidRequestError

from app.config import session, logger
from app.db import sessionDB, Coin
from app.service import (
    validate_symbol, balance_coin, get_min_limit)


# Процент снижения для поуцпки -5% (-5% по умолчанию 0.95)
PROCENT_BUY = float(os.getenv('PROCENT_BUY', '0.95'))
# Процент роста для продажи +5% (+5% по умолчанию 1.05)
PROCENT_SELL = float(os.getenv('PROCENT_SELL', '1.05'))
# USDT на которую будет покупаться монета
BUY_USDT = int(os.getenv('BUY_USDT', '5'))
# Комиссия на покупку 0.1% (по умолчанию 0.999)
COMMISSION = float(os.getenv('COMMISSION', '0.999'))


def get_balance():
    """Получить список монет"""
    response = session.get_wallet_balance(accountType="UNIFIED")
    response = response['result']['list'][0]['coin']
    if not response:
        print('💼 В портфеле пока нет монет.')
        return
    result = '💰 Ваш крипто-портфель:\n'
    for value in response:
        result += (
            f'''
            -------- 🪙  {value['coin']} --------
            🔹 Баланс: {value['walletBalance']}
            💵 Оценка в USD: {value['usdValue']}
            '''
        )
        # pprint(coin)
    print(result)


def list_coins():
    """Получить список монет из базы данных"""
    result = sessionDB.execute(
        select(Coin)).scalars().all()
    if not result:
        print('📦 В базе данных нет ни одной монеты.')
        return
    result_log = '📊 Монеты, сохранённые в базе данных:\n'
    for coin in result:
        price_buy = f'{coin.price_buy:.8f}' if coin.price_buy else None
        coin.stop = 'остановлено ⛔️' if coin.stop else 'в работе 🔄'
        result_log += f'''
        -------- 🪙  {coin.name} --------
        🆔 id: {coin.id}
        🔹 Баланс: {coin.balance:.8f}
        💵 Курс стартовой покупки: {coin.start:.8f}
        💵 Курс последней покупки: {price_buy}
        💸 Затрачено: {coin.payback:.8f}
        Статус: {coin.stop}
        '''
    print(result_log)


def get_info_coin(symbol='BTCUSDT'):
    """Узнать cтоимость монеты и лимиты"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        return
    ticker = ticker['result']['list'][0]
    info = session.get_instruments_info(category="spot", symbol=symbol)
    # pprint(info)
    min_order_usdt = info["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"]
    min_order_coin = info["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]
    base_precision = info["result"]["list"][0]["lotSizeFilter"]["basePrecision"]
    base_precision = abs(decimal.Decimal(
        str(base_precision)).as_tuple().exponent)
    return {
        'lastPrice': ticker["lastPrice"],
        'min_usdt': min_order_usdt,
        'min_coin': min_order_coin,
        'base_precision': base_precision,
        'symbol': symbol,
        'info': (
            f'--- Информация о {ticker['symbol']}---\n'
            f'Рыночная цена: {ticker["lastPrice"]} USDT\n'
            f'Минимальный ордер: {min_order_usdt} USDT или '
            f'{min_order_coin} {ticker['symbol']}'
        )
    }


def get_add_coin(symbol='BTCUSDT'):
    """Добавить монету"""
    ticker = get_info_coin(symbol)
    if not ticker:
        return

    balance = balance_coin(session, symbol)
    if not balance:
        return

    result = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()

    if result is None:
        if get_min_limit(BUY_USDT, ticker):
            return

        new_coin = Coin(
            name=symbol,
            start=ticker["lastPrice"],
            balance=balance['walletBalance'],
            payback=-abs(
                float(balance['walletBalance']) * float(ticker["lastPrice"]))
        )
        sessionDB.add(new_coin)
        sessionDB.commit()
        logger.info(f'✅ {symbol} добавлен в базу данных')
    else:
        print(f'{symbol} уже есть в базе данных')


def get_bot_start():
    """Запуск бота"""
    result = sessionDB.execute(
        select(Coin).where(Coin.stop.is_(False))).scalars().all()
    if not result:
        logger.error('❌ В базе данных нет активных монет. ')
        return False

    for coin in result:
        ticker = get_info_coin(coin.name)
        if get_min_limit(BUY_USDT, ticker):
            sessionDB.execute(update(Coin).where(
                Coin.name == coin.name).values(stop=True))
            sessionDB.commit()
            continue

        if float(ticker["lastPrice"]) >= (coin.start * PROCENT_SELL):
            logger.info(f'Продаем {coin.name}')
            price_coin = round(coin.balance, ticker['base_precision'])
            price_coin = (
                math.floor(coin.balance * 10**ticker['base_precision']))
            price_coin = price_coin / 10**ticker['base_precision']
            if ticker['base_precision'] == 0:
                price_coin = int(price_coin)
            sell_coin(coin.name, price_coin)
        else:
            price_buy = coin.price_buy if coin.price_buy else coin.start
            if float(ticker["lastPrice"]) <= (price_buy * PROCENT_BUY):
                logger.info(f'Покупаем {coin.name}')
                buy_coin(coin.name, BUY_USDT)
    return True


def buy_coin(symbol, price):
    """Купить монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        # Проверка символа на корректность
        return
    result = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()
    try:
        session.place_order(
            category="spot",
            symbol=symbol,
            side="Buy",
            orderType="Market",
            qty=str(price)
        )
    except InvalidRequestError as e:
        if "170131" in str(e):
            result.start = True
            logger.error("Недостаточно средств на балансе для покупки.")
        else:
            logger.error(f'Ошибка при покупке монеты: {str(e)}')
    else:
        ticker = ticker["result"]["list"][0]
        logger.info(
            f"✅ Куплено {symbol} на {price * COMMISSION} USDT"
            f' по цене {ticker["lastPrice"]}')
        balance = balance_coin(session, symbol)
        result.price_buy = ticker["lastPrice"]
        result.balance = balance['walletBalance']
        result.payback -= price
    sessionDB.commit()


def sell_coin(symbol, price):
    """Продать монету"""
    ticker = validate_symbol(session, symbol)
    if not ticker:
        # Проверка символа на корректность
        return
    result = sessionDB.execute(
        select(Coin).where(Coin.name == symbol)
    ).scalars().first()
    try:
        session.place_order(
            category="spot",
            symbol=symbol,
            side="Sell",
            orderType="Market",
            qty=str(price)
        )
    except InvalidRequestError as e:
        logger.error(f'Ошибка при продаже монеты: {str(e)}')
    else:
        ticker = ticker["result"]["list"][0]
        logger.info(
            f"✅ Продано {price} {symbol}"
            f' по цене {ticker["lastPrice"]}')
        balance = balance_coin(session, symbol)
        result.balance = balance['walletBalance']
        result.payback += price * float(ticker["lastPrice"])
        result.stop = True
    sessionDB.commit()


def get_delete_coin(id_coin):
    """ Удалить монету из базы данных """
    result = sessionDB.execute(
        select(Coin).where(Coin.id == id_coin)
    ).scalars().first()
    if result is None:
        print(
            f"❌ Монеты с id {id_coin}, нет в базе данных")
        return
    logger.info(f"{result.name} - монета удалена из базы данных")
    sessionDB.delete(result)
    sessionDB.commit()


def get_update_coin(id_coin, param):
    """ Изменить монету в базе данных """
    result = sessionDB.execute(
        select(Coin).where(Coin.id == id_coin)
    ).scalars().first()
    if result is None:
        print(
            f"❌ Монеты с id {id_coin}, нет в базе данных")
        return

    if 'help' in param:
        print(
            f'ℹ️  Доступные параметры для изменения монеты {result.name}:\n\n'
            'start — курс первой (стартовой) покупки (пример: start=0.00123)\n'
            'buy — курс последней покупки (пример: buy=0.00110)\n'
            'pay — общая сумма затрат на покупку монеты (пример: pay=150.50)\n'
            'stop — 0 торговать или 1 остановить'
            '\nПример использования: '
            f'python main.py -e 1 -p start=0.00123 buy=0.00110\n'
            'Можно указать только нужные параметры.')
        return

    param_dict = {
        'start': None,
        'buy': None,
        'pay': None,
        'stop': None
    }
    for item in param:
        if '=' not in item:
            print(
                f'❌ Некорректный параметр: "{item}". '
                'Ожидается формат ключ=значение. Введите help для помощи')
            return

        key, value = item.split('=', 1)
        if key not in param_dict:
            print(
                f'❌ Недопустимый ключ: "{key}". '
                f'Разрешены только: {", ".join(param_dict.keys())}.')
            return

        try:
            param_dict[key] = float(value)
        except ValueError:
            print(f'❌ Значение для "{key}" должно быть числом.')
            return

    if param_dict['start'] is not None:
        result.start = param_dict['start']
    if param_dict['buy'] is not None:
        result.price_buy = param_dict['buy']
    if param_dict['pay'] is not None:
        result.payback = param_dict['pay']
    if param_dict['stop'] is not None:
        param_dict['stop'] = False if int(param_dict['stop']) == 0 else True
        result.stop = param_dict['stop']
    sessionDB.commit()
    print(f'✅ Монета {result.name} успешно обновлена')
