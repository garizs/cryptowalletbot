import requests
from datetime import datetime, timezone
from traceback import print_exc


def final_balance(wallet: str, btc: bool = True):
    try:
        api_link = "https://blockchain.info/q/addressbalance/"

        request = requests.get(api_link + wallet + "?confirmations=6")
        satoshi_confirmado = int(request.text)

        btc_confirmada = satoshi_confirmado / 100000000

        if btc:
            return btc_confirmada
        else:
            return satoshi_confirmado
    except:
        print_exc()
        return None


def convert_to_money(value, currency):
    api_link = "https://blockchain.info/ticker"

    request = requests.get(api_link)
    result_list = request.json()
    btc_value = result_list[currency]["15m"]

    final_value = round(value * btc_value, 2)

    return final_value, btc_value
