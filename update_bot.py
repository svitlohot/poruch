import os
import requests
from PIL import Image, ImageDraw, ImageFont

def get_rates():
    try:
        res = requests.get('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5').json()
        usd = next(item for item in res if item['ccy'] == 'USD')
        return f"USD: {float(usd['buy']):.2f} / {float(usd['sale']):.2f}"
    except:
        return "USD: Недоступно"

def create_image(rate_text):
    # Створюємо чисте зображення (сірий фон, наприклад #2F3136)
    width, height = 1024, 512
    image = Image.new("RGB", (width, height), "#2F3136")
    draw = ImageDraw.Draw(image)
    
    # Малюємо фірмову бурштингову плашку вгорі (#FFBF00)
    draw.rectangle([0, 0, width, 80], fill="#FFBF00")
    
    # Використовуємо дефолтний шрифт Pillow (щоб не завантажувати сторонні файли)
    # Текст заголовка
    draw.text((30, 25), "СТАН ГРОМАДИ ХОТЯНІВКА", fill="#2F3136")
    
    # Текст курсу валют
    draw.text((50, 150), f"  Курс валют (ПриватБанк):", fill="#FFFFFF")
    draw.text((50, 200), f"   {rate_text}", fill="#FFBF00")
    
    # Сюди в майбутньому допишемо погоду, тривоги чи камери
    draw.text((50, 300), "🌳 Повітря: Чисте (EcoCity)", fill="#FFFFFF")
    
    # Зберігаємо картинку в корінь репозиторію
    image.save("status.png")
    print("Картинку status.png успішно згенеровано!")

rate_string = get_rates()
create_image(rate_string)
