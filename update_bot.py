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

def create_image(rate_text):
    # Фірмова палітра "Поруч"
    BG_COLOR = "#FDF8ED"      # М'який кремовий фон
    CARD_COLOR = "#054538"    # Глибокий смарагдово-зелений
    TEXT_LIGHT = "#FDF8ED"    # Світлий текст для плашок
    TEXT_DARK = "#054538"     # Темний текст для заголовків

    # 1. Створюємо вертикальне зображення (Портретний формат для телефонів)
    width, height = 600, 1024
    image = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(image)
    
    font_path = "Montserrat-Bold.ttf" 
    
    try:
        # Збільшені розміри шрифтів для максимальної читабельності
        font_title = ImageFont.truetype(font_path, 38)
        font_subtitle = ImageFont.truetype(font_path, 24)
        font_data = ImageFont.truetype(font_path, 34)
        font_small = ImageFont.truetype(font_path, 20)
    except IOError:
        font_title = font_subtitle = font_data = font_small = ImageFont.load_default()

    # 2. Головний заголовок (розбиваємо на два рядки для балансу)
    draw.text((50, 50), "СТАН ГРОМАДИ", fill=TEXT_DARK, font=font_title)
    draw.text((50, 100), "ХОТЯНІВКА", fill=TEXT_DARK, font=font_title)
    
    # 3. Блок: Курс Валют
    # Координати: [ліво, верх, право, низ]
    draw.rounded_rectangle([40, 190, 560, 340], radius=18, fill=CARD_COLOR)
    draw.text((70, 215), "Курс валют (ПриватБанк):", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 260), f"USD: {rate_text}", fill=TEXT_LIGHT, font=font_data)
    
    # 4. Блок: Стан повітря
    draw.rounded_rectangle([40, 370, 560, 520], radius=18, fill=CARD_COLOR)
    draw.text((70, 395), "Стан повітря (Вишгород):", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 440), "Повітря: Чисте (SaveEcobot)", fill=TEXT_LIGHT, font=font_data)

    # 5. Тимчасовий пустий блок під Тривоги (щоб ти бачив, де він буде)
    draw.rounded_rectangle([40, 550, 560, 700], radius=18, fill=CARD_COLOR)
    draw.text((70, 575), "Повітряна тривога:", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 620), "Очікування даних API...", fill=TEXT_LIGHT, font=font_data)

    # 6. Час оновлення внизу (без слова "Київський час")
    kyiv_time = datetime.utcnow() + timedelta(hours=3)
    current_time = kyiv_time.strftime("%d.%m.%Y %H:%M")
    draw.text((40, 950), f"Дані на: {current_time}", fill="#888888", font=font_small)
    
    # Зберігаємо
    image.save("status.png")
    print("Новий вертикальний інформер успішно згенеровано!")

rate_string = get_rates()
create_image(rate_string)
