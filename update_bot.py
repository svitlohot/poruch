import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def get_rates():
    try:
        res = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5').json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return f"{float(usd['buy']):.2f} / {float(usd['sale']):.2f}"
    except:
        return "Недоступно"

def create_image(rate_text):
    BG_COLOR = "#FDF8ED"      # М'який кремовий фон
    CARD_COLOR = "#054538"    # Глибокий смарагдово-зелений
    TEXT_LIGHT = "#FDF8ED"    # Світлий текст
    TEXT_導K = "#054538"     # Темний текст

    width, height = 1024, 600
    image = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    font_path = "Montserrat-Bold.ttf" 
    
    try:
        font_title = ImageFont.truetype(font_path, 36)
        font_data = ImageFont.truetype(font_path, 28)
        font_small = ImageFont.truetype(font_path, 18)
    except IOError:
        font_title = font_data = font_small = ImageFont.load_default()

    # 1. Головний заголовок
    draw.text((50, 40), "СТАН ГРОМАДИ ХОТЯНІВКА", fill=TEXT_DARK, font=font_title)
    
    # 2. Плашка для Курсу Валют
    draw.rounded_rectangle([50, 120, 974, 250], radius=15, fill=CARD_COLOR)
    draw.text((80, 140), "Курс валют (ПриватБанк):", fill=TEXT_LIGHT, font=font_small)
    draw.text((80, 180), f"USD: {rate_text}", fill=TEXT_LIGHT, font=font_data)
    
    # 3. Плашка для Екології (Прибрали емодзі дерева, щоб не було квадратика)
    draw.rounded_rectangle([50, 280, 974, 410], radius=15, fill=CARD_COLOR)
    draw.text((80, 300), "Стан повітря (EcoCity):", fill=TEXT_LIGHT, font=font_small)
    draw.text((80, 340), "Повітря: Чисте (Заводська, 12)", fill=TEXT_LIGHT, font=font_data)

    # 4. Внизу плашка з часом оновлення (Фікс таймзони на Київ UTC+3)
    # Зсуваємо час сервера на 3 години вперед для літнього часу в Україні
    from datetime import datetime, timedelta
    kyiv_time = datetime.utcnow() + timedelta(hours=3)
    current_time = kyiv_time.strftime("%d.%m.%Y %H:%M")
    
    draw.text((50, 530), f"Дані на: {current_time} (Київський час)", fill="#888888", font=font_small)
    
    image.save("status.png")
    print("Картинку успішно оновлено з урахуванням таймзони!")

rate_string = get_rates()
create_image(rate_string)
