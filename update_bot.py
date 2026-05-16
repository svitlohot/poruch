import os
import requests

CLIENT_ID = os.getenv('SP_ID')
CLIENT_SECRET = os.getenv('SP_SECRET')

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

def update_global_variable(token, var_name, var_value):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {"variable_value": var_value}
    url = f'https://api.sendpulse.com/telegram/variables/set-global-variable?variable_name={var_name}'
    response = requests.post(url, headers=headers, json=payload)
    print(f"Оновлення {var_name}: {response.status_code} - {response.text}")

token = get_token()
if token:
    rate_string = get_rates()
    # Назва змінної повинна точно збігатися з тим, що створено в SendPulse (наприклад, exchange_rate)
    update_global_variable(token, 'exchange_rate', rate_string)
else:
    print("Не вдалося отримати токен доступу SendPulse")
