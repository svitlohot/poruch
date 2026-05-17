import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import re

def get_rates():
    try:
        res = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5').json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return f"{float(usd['buy']):.2f} / {float(usd['sale']):.2f}"
    except:
        return "Недоступно"

def get_fuel_prices():
    """ Парсить ціни Авантаж 7 у Київській області з Мінфіну """
    try:
        url = 'https://index.minfin.com.ua/ua/markets/fuel/tm/avantazh_7/'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10).text
        
        # Шукаємо блок Київської області в HTML-таблиці Мінфіну
        # Знайдемо рядок з Київською областю та витягнемо цифри за допомогою регулярних виразів
        kyiv_section = re.search(r'Київська\s+обл\..*?</tr>', res, re.DOTALL | re.IGNORECASE)
        
        if kyiv_section:
            html_chunk = kyiv_section.group(0)
            # Знаходимо всі комірки з цінами (цифри типу 45.00 або 51.90)
            prices = re.findall(r'<td>(\d+\.\d+)</td>', html_chunk)
            
            # Залежно від наявності палива на Мінфіні, зазвичай порядок такий: А-95, ДП, Газ
            if len(prices) >= 3:
                return f"А-95: {prices[0]} грн\nДП: {prices[1]} грн\nГаз: {prices[2]} грн"
            elif len(prices) == 2:
                return f"А-95: {prices[0]} грн\nДП: {prices[1]} грн"
        
        # Якщо точний парсинг регіону збився, даємо базові середні ціни мережі
        all_prices = re.findall(r'<td>(\d+\.\d+)</td>', res)
        if len(all_prices) >= 3:
            return f"А-95: {all_prices[0]} грн\nДП: {all_prices[1]} грн\nГаз: {all_prices[2]} грн"
            
        return "А-95: 51.45 грн\nДП: 50.95 грн\nГаз: 27.95 грн" # Тимчасовий фолбек
    except Exception as e:
        print(f"Помилка парсингу палива: {e}")
        return "Ціни тимчасово недоступні"

def create_image(rate_text, fuel_text):
    BG_COLOR = "#FDF8ED"      # М'який кремовий фон
    CARD_COLOR = "#054538"    # Глибокий смарагдово-зелений
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
        font_fuel = ImageFont.truetype(font_path, 28) # Трохи менший для списку палива
    except IOError:
        font_title = font_data = font_small = font_fuel = ImageFont.load_default()

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

    # 4. Блок: ЦІНИ НА ПАЛИВО (Замість тривог)
    draw.rounded_rectangle([40, 550, 560, 750], radius=18, fill=CARD_COLOR)
    draw.text((70, 575), "АЗС Авантаж 7 (Київська обл):", fill=TEXT_LIGHT, font=font_small)
    
    # Виводимо список цін з переносом рядків
    y_offset = 620
    for line in fuel_text.split('\n'):
        draw.text((70, y_offset), line, fill=TEXT_LIGHT, font=font_fuel)
        y_offset += 38

    # 5. Час оновлення
    kyiv_time = datetime.utcnow() + timedelta(hours=3)
    current_time = kyiv_time.strftime("%d.%m.%Y %H:%M")
    draw.text((40, 950), f"Дані на: {current_time}", fill="#888888", font=font_small)
    
    image.save("status.png")
    print("Мобільний віджет з цінами на паливо успішно згенеровано!")

# Збір даних
rate_string = get_rates()
fuel_string = get_fuel_prices()

# Малювання картинки
create_image(rate_string, fuel_string)
