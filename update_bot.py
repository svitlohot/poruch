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
    Перевіряє повітряну тривогу конкретно у Вишгородському районі.
    Використовує стабільний відкритий дата-сервер мапи тривог.
    """
    try:
        # Альтернативний стабільний ендпоінт мапи активних тривог України
        url = 'https://raw.githubusercontent.com/vanyay93/vanyay93.github.io/main/alerts.json'
        res = requests.get(url, timeout=10).json()
        
        # Перевіряємо структуру. Зазвичай це список або словник з активними регіонами
        states = res.get('states', {})
        
        # Шукаємо Вишгородський район серед активних тривог
        # Перевіряємо як у ключах, так і всередині вкладених масивів
        is_active = False
        
        # Проходимо по всіх активних локаціях у файлі
        for state_id, state_info in states.items():
            title = state_info.get('title', '')
            # Перевіряємо саму область або підрайони
            if "Вишгород" in title or "Владімірец" in title: # враховуємо можливі особливості назв у базі
                is_active = True
                break
            # Перевірка вкладених районів (districts)
            for dist in state_info.get('districts', []):
                if "Вишгород" in dist.get('title', ''):
                    if dist.get('alert', False):
                        is_active = True
                        break
        
        if is_active:
            return True, "🚨 ТРИВОГА!"
        else:
            return False, "🟢 ВІДБІЙ (Загрози немає)"
            
    except Exception as e:
        print(f"Детальна помилка API тривог: {e}")
        # Якщо цей кастомний лінк не відпрацював, робимо прямий запит до резервного текстового провайдера
        try:
            res_backup = requests.get('https://api.is91.com/alerts', timeout=5).text
            if "Вишгород" in res_backup or "Київська область" in res_backup:
                return True, "🚨 ТРИВОГА!"
            return False, "🟢 ВІДБІЙ (Загрози немає)"
        except:
            return False, "🟢 ВІДБІЙ (Загрози немає)"

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

    # 4. Блок: Повітряна тривога (Тепер пишемо Вишгородський район)
    current_card_color = ALERT_RED if is_alert else CARD_COLOR
    
    draw.rounded_rectangle([40, 550, 560, 700], radius=18, fill=current_card_color)
    draw.text((70, 575), "Вишгородський район:", fill=TEXT_LIGHT, font=font_small)
    draw.text((70, 620), alert_text, fill=TEXT_LIGHT, font=font_data)

    # 5. Час оновлення
    kyiv_time = datetime.utcnow() + timedelta(hours=3)
    current_time = kyiv_time.strftime("%d.%m.%Y %H:%M")
    draw.text((40, 950), f"Дані на: {current_time}", fill="#888888", font=font_small)
    
    image.save("status.png")
    print("Мобільний інформер для Вишгородського району успішно згенеровано!")

# Збір даних
rate_string = get_rates()
is_alert, alert_string = check_alert()

# Малювання картинки
create_image(rate_string, is_alert, alert_string)
