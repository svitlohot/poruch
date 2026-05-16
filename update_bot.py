import os
import requests

CLIENT_ID = os.getenv('SP_ID')
CLIENT_SECRET = os.getenv('SP_SECRET')

# !!! СЮДИ ВСТАВ ID СВОГО БОТА (цифри з адресного рядка, наприклад, 12345)
BOT_ID = "69df205225c75c5ed3048310" 

def get_token():
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post('https://api.sendpulse.com/oauth/access_token', json=data)
    return response.json().get('access_token')

def get_rates():
    try:
        res = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5').json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return f"{float(usd['buy']):.2f} / {float(usd['sale']):.2f}"
    except Exception as e:
        print(f"Помилка Привату: {e}")
        return "Недоступно"

def update_bot_global_variable(token, bot_id, var_name, var_value):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        "name": var_name,
        "value": var_value
    }
    # ОФІЦІЙНИЙ ПРАВИЛЬНИЙ URL ДЛЯ ГЛОБАЛЬНИХ ЗМІННИХ БОТА
    url = f'https://api.sendpulse.com/telegram/bots/{bot_id}/variables'
    response = requests.post(url, headers=headers, json=payload)
    print(f"Результат оновлення глобальної змінної: {response.status_code} - {response.text}")

token = get_token()
if token:
    rate_string = get_rates()
    # Передаємо назву глобальної змінної, яку ми створили на першому кроці
    update_bot_global_variable(token, BOT_ID, 'exchange_rate', rate_string)
else:
    print("Не вдалося отримати токен доступу SendPulse")
