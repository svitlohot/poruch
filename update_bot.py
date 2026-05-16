import os
import requests

CLIENT_ID = os.getenv('SP_ID')
CLIENT_SECRET = os.getenv('SP_SECRET')
# Встав сюди свій contact_id з адресного рядка SendPulse (довгий рядок букв/цифр)
CONTACT_ID = "69df205225c75c5ed3048310" 

def get_token():
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post('https://api.sendpulse.com/oauth/access_token', json=data)
    
    # Цей рядок покаже нам в логах Гітхабу реальну помилку від SendPulse
    print(f"Відповідь сервера авторизації: Status {response.status_code}, Body: {response.text}")
    
    return response.json().get('access_token')

def get_rates():
    try:
        res = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5').json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return f"{float(usd['buy']):.2f} / {float(usd['sale']):.2f}"
    except Exception as e:
        print(f"Помилка Привату: {e}")
        return "Недоступно"

def update_variable(token, var_name, var_value):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        "contact_id": CONTACT_ID,
        "variables": [
            {"name": var_name, "value": var_value}
        ]
    }
    # Використовуємо залізобетонний метод оновлення змінної для контакту
    url = 'https://api.sendpulse.com/telegram/contacts/set-variable'
    response = requests.post(url, headers=headers, json=payload)
    print(f"Оновлення контакту: {response.status_code} - {response.text}")

token = get_token()
if token:
    rate_string = get_rates()
    update_variable(token, 'exchange_rate', rate_string)
else:
    print("Не вдалося отримати токен доступу")
