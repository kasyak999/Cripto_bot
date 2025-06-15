from pprint import pprint
from app.config import session


if __name__ == '__main__':
    # pprint(session)
    print('')
    response = session.get_wallet_balance(accountType="UNIFIED")
    pprint(response)
