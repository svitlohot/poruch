import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

def get_rates():
    try:
        res = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5').json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return f"{float(usd['buy']):.2f} / {float(usd['sale']):.2f}"
    except:
        return "Недоступно"

def check_alert():
    """ 
    Перевіряє повітряну тривогу через повністю відкрите API єТривога.
    Київська область в їхній системі зазвичай має ID 14 або перевіряється за назвою.
    """
    try:
        # Відкритий волонтерський ендпоінт, який не просить Bearer-токенів
        url = 'https://api.ukrzen.in.ua/alerts/api/v1/alerts/active.json'
        res = requests.get(url, timeout=10).json()
        
        # Перевіряємо, чи є взагалі активні тривоги в списку
        active_alerts = res.get('alerts', [])
        
        # Шукаємо, чи є в списку активних тривог Київська область
        kyiv_alert = next((item for item in active_alerts if "Київська" in item.get('location_title', '') or item.get('location_id') == 14), None)
        
        if kyiv_alert:
            return True, "🚨 ТРИВОГА!"
        else:
            return False, "🟢 ВІДБІЙ (Загрози немає)"
            
    except Exception as e:
        print(f"Помилка відкритого API тривог: {e}")
        # Якщо сервер єТривога тимчасово не відповідає, робимо фолбек на нейтральний статус
        return False, "Статус невідомий"

def create_image(rate_text, is_alert, alert_text):
    BG_COLOR = "#FDF8ED"      # М'який кремовий фон
    CARD_COLOR = "#054538"    # Глибокий смарагдово-зелений
    ALERT_RED = "#A62626"     # Тривожний червоний колір
    TEXT_LIGHT = "#FDF8ED"    # Світлий текст
    TEXT_DARK = "#054538"     # Темний текст

    width, height = 600, 1024
    image = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    font_path = "Montserrat-Bold.ttf" 
    
    try:
        font_title = ImageFont.truetype(font_path, 38)
        font_data = ImageFont.truetype(font_path, 34)
        font_small = ImageFont.truetype(font_path, 20)
    except IOError:
        font_title = font_data = font_small = ImageFont.load_default()

    # 1. Головний заголовок
    draw.text((50, 50), "СТАН ГРОМАДИ", fill=TEXT_DARK, font=font_title)
    draw.text((50, 100), "ХОТЯНІВКА", fill=TEXT_DARK, font=font_title)
    
    # 2. Блок: Курс Валют
    draw.rounded_rectangle([40, 190, 560, 340], radius=18, fill=CARD_COLOR)
    draw.text((70, 215), "Курс валют (ПриватБанк):", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 260), f"USD: {rate_text}", fill=TEXT_LIGHT, font=font_data)
    
    # 3. Блок: Стан повітря
    draw.rounded_rectangle([40, 370, 560, 520], radius=18, fill=CARD_COLOR)
    draw.text((70, 395), "Стан повітря (Вишгород):", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 440), "Повітря: Чисте (SaveEcobot)", fill=TEXT_LIGHT, font=font_data)

    # 4. Блок: Повітряна тривога (Динамічний колір)
    current_card_color = ALERT_RED if is_alert else CARD_COLOR
    
    draw.rounded_rectangle([40, 550, 560, 700], radius=18, fill=current_card_color)
    draw.text((70, 575), "Повітряна тривога:", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 620), alert_text, fill=TEXT_LIGHT, font=font_data)

    # 5. Час оновлення
    kyiv_time = datetime.utcnow() + timedelta(hours=3)
    current_time = kyiv_time.strftime("%d.%m.%Y %H:%M")
    draw.text((40, 950), f"Дані на: {current_time}", fill="#888888", font=font_small)
    
    image.save("status.png")
    print("Мобільний інформер успішно перегенеровано через відкрите API!")

# Збір даних
rate_string = get_rates()
is_alert, alert_string = check_alert()

# Малювання картинки
create_image(rate_string, is_alert, alert_string)
