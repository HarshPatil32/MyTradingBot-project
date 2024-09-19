import requests

url = "https://paper-api.alpaca.markets/v2/orders"

headers = {
    "APCA-API-KEY-ID": "PKGDSHK8BUDWJY21N4ZX",
    "APCA-API-SECRET-KEY": "ER3NWL6YNNules0rg33SihD13WHyquJq2gzTEG8Z"
}

data = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "type": "market",
    "time_in_force": "gtc"
}

response = requests.post(url, headers=headers, json=data)

print(response.json())