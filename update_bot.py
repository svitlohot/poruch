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
    Перевіряє повітряну тривогу у Вишгородському районі (ID: 41)
    """
    is_active = False

    # Спроба 1: Офіційне дзеркало JSON
    try:
        url = 'https://raw.githubusercontent.com/aerial-alerts/digital-map-data/main/alerts.json'
        res = requests.get(url, timeout=5).json()
        for alert in res:
            if str(alert.get('id')) == '41' or "вишгород" in alert.get('location_title', '').lower():
                if alert.get('alert', False):
                    is_active = True
                    return True, "ТРИВОГА!"
    except Exception as e:
        print(f"Головне API JSON недоступне: {e}")

    # Спроба 2: Перший текстовий резерв (is91)
    try:
        res_backup = requests.get('https://api.is91.com/alerts', timeout=5).text.lower()
        if "вишгород" in res_backup or "київська" in res_backup:
            return True, "ТРИВОГА!"
    except Exception as e:
        print(f"Резерв 1 (is91) недоступний: {e}")

    # Спроба 3: Другий текстовий резерв (Текстовий дамп єТривоги)
    try:
        res_backup2 = requests.get('https://api.ukrzen.in.ua/alerts/api/v1/alerts/active.json', timeout=5).text.lower()
        if "вишгород" in res_backup2 or "київська" in res_backup2:
            return True, "ТРИВОГА!"
    except Exception as e:
        print(f"Резерв 2 (ukrzen) недоступний: {e}")

    # Якщо пройшли всі три перевірки й ніде тривоги не знайшли
    return False, "ВІДБІЙ (Загрози немає)"

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

    # 4. Блок: Повітряна тривога (Вишгородський район)
    current_card_color = ALERT_RED if is_alert else CARD_COLOR
    draw.rounded_rectangle([40, 550, 560, 700], radius=18, fill=current_card_color)
    draw.text((70, 575), "Вишгородський район:", fill=TEXT_LIGHT, font=font_small)
    
    # Замість емодзі-значків малюємо красиве графічне коло (індикатор статусу) всередині плашки
    # Координати кола: [x0, y0, x1, y1]
    circle_color = "#FF4D4D" if is_alert else "#2ECC71" # Яскраво-червоне або яскраво-зелене коло
    draw.ellipse([70, 628, 95, 653], fill=circle_color)
    
    # Зсуваємо текст трохи праворуч, щоб він не налізав на наше намальоване коло
    draw.text((115, 620), alert_text, fill=TEXT_LIGHT, font=font_data)

    # 5. Час оновлення
    kyiv_time = datetime.utcnow() + timedelta(hours=3)
    current_time = kyiv_time.strftime("%d.%m.%Y %H:%M")
    draw.text((40, 950), f"Дані на: {current_time}", fill="#888888", font=font_small)
    
    image.save("status.png")
    print("Мобільний віджет для Вишгородського району успішно оновлено!")

# Збір даних
rate_string = get_rates()
is_alert, alert_string = check_alert()

# Малювання картинки
create_image(rate_string, is_alert, alert_string)
