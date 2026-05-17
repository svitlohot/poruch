import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ============================================
# НАСТРОЙКИ
# ============================================

WIDTH = 1080
HEIGHT = 1350

BG = "#F5F1E8"
CARD = "#FFFDFC"
BORDER = "#D9D4CA"

TEXT = "#0D4B3E"
SUBTEXT = "#4F7A6F"

GREEN = "#DDF4D7"
RED = "#F8D7D7"
YELLOW = "#F5E7B8"
BLUE = "#DCE8F5"
PURPLE = "#E8DDF5"

# ============================================
# ДАНІ
# ============================================

def get_currency():
    try:
        url = "https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5"
        data = requests.get(url, timeout=5).json()

        usd = next(x for x in data if x["ccy"] == "USD")
        eur = next(x for x in data if x["ccy"] == "EUR")

        return {
            "usd": round(float(usd["sale"]), 2),
            "eur": round(float(eur["sale"]), 2)
        }

    except Exception as e:
        print("Currency error:", e)

        return {
            "usd": "—",
            "eur": "—"
        }


def get_fuel():
    # поки заглушка
    return {
        "a95": "55.90",
        "station": "Авантаж 7"
    }


def get_air():
    # заглушка
    return {
        "aqi": 62,
        "status": "Добре"
    }


def get_alert():
    # заглушка
    return {
        "active": False
    }


def get_power():
    try:
        channel_key = os.environ.get("SVITLO_KEY", "EADAEFAUAF")
        url = f"https://api.svitlobot.in.ua/status?channel_key={channel_key}"
        text = requests.get(url, timeout=5).text

        if "світло є" in text.lower():
            return {"status": "Є", "desc": "Стабільно"}
        elif "світла немає" in text.lower():
            return {"status": "Немає", "desc": "Відключено"}
        else:
            return {"status": "—", "desc": "Невідомо"}

    except Exception as e:
        print("Power error:", e)
        return {"status": "—", "desc": "Помилка"}


def get_traffic():
    # заглушка
    return {
        "time": "38 хв",
        "route": "через Вишгород",
        "delay": "+4 хв затримка"
    }

# ============================================
# UI
# ============================================

img = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

FONT_PATH = "Montserrat-Bold.ttf"

try:
    title_font = ImageFont.truetype(FONT_PATH, 76)
    h2_font = ImageFont.truetype(FONT_PATH, 36)
    big_font = ImageFont.truetype(FONT_PATH, 64)
    medium_font = ImageFont.truetype(FONT_PATH, 30)
    small_font = ImageFont.truetype(FONT_PATH, 24)

except:
    title_font = ImageFont.load_default()
    h2_font = ImageFont.load_default()
    big_font = ImageFont.load_default()
    medium_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

# ============================================
# HEADER
# ============================================

draw.text((70, 60), "ПОРУЧ", fill=TEXT, font=title_font)

draw.text(
    (70, 150),
    "СТАН ГРОМАДИ",
    fill=TEXT,
    font=h2_font
)

draw.text(
    (70, 205),
    "Хотянівка • Вишгород",
    fill=SUBTEXT,
    font=medium_font
)

now = datetime.utcnow() + timedelta(hours=3)

draw.text(
    (820, 70),
    "Оновлено",
    fill=SUBTEXT,
    font=small_font
)

draw.text(
    (820, 120),
    now.strftime("%d.%m.%Y"),
    fill=TEXT,
    font=medium_font
)

draw.text(
    (820, 180),
    now.strftime("%H:%M"),
    fill=TEXT,
    font=big_font
)

# ============================================
# CARD FUNCTION
# ============================================

def card(x, y, w, h, title, value, subtitle, color):

    draw.rounded_rectangle(
        [x, y, x+w, y+h],
        radius=34,
        fill=CARD,
        outline=BORDER,
        width=2
    )

    # status circle
    draw.ellipse(
        [x+35, y+35, x+135, y+135],
        fill=color
    )

    # title
    draw.text(
        (x+165, y+45),
        title,
        fill=TEXT,
        font=h2_font
    )

    # value
    draw.text(
        (x+165, y+105),
        value,
        fill=TEXT,
        font=big_font
    )

    # subtitle
    draw.text(
        (x+165, y+190),
        subtitle,
        fill=SUBTEXT,
        font=medium_font
    )

# ============================================
# DATA
# ============================================

currency = get_currency()
fuel = get_fuel()
air = get_air()
alert = get_alert()
power = get_power()
traffic = get_traffic()

# ============================================
# CARDS
# ============================================

LEFT = 50
RIGHT = 545

TOP = 320
STEP = 280

CARD_W = 485
CARD_H = 240

# 1 Свет
card(
    LEFT,
    TOP,
    CARD_W,
    CARD_H,
    "1. СВІТЛО",
    power["status"],
    f"🟢 {power['desc']}",
    GREEN
)

# 2 Тривога
alert_text = "НЕМАЄ"
alert_sub = "🟢 Тихо"

alert_color = GREEN

if alert["active"]:
    alert_text = "ТРИВОГА"
    alert_sub = "🔴 Увага"
    alert_color = RED

card(
    RIGHT,
    TOP,
    CARD_W,
    CARD_H,
    "2. ТРИВОГА",
    alert_text,
    alert_sub,
    alert_color
)

# 3 Валюта
card(
    LEFT,
    TOP + STEP,
    CARD_W,
    CARD_H,
    "3. КУРС",
    f"USD {currency['usd']}",
    f"EUR {currency['eur']}",
    BLUE
)

# 4 Паливо
card(
    RIGHT,
    TOP + STEP,
    CARD_W,
    CARD_H,
    "4. ПАЛИВО",
    f"A95 {fuel['a95']}",
    fuel["station"],
    YELLOW
)

# 5 Повітря
air_color = GREEN

if air["aqi"] > 100:
    air_color = YELLOW

if air["aqi"] > 150:
    air_color = RED

card(
    LEFT,
    TOP + STEP*2,
    CARD_W,
    CARD_H,
    "5. ПОВІТРЯ",
    f"AQI {air['aqi']}",
    air["status"],
    air_color
)

# 6 Дорога
card(
    RIGHT,
    TOP + STEP*2,
    CARD_W,
    CARD_H,
    "6. ДО КИЄВА",
    traffic["time"],
    traffic["delay"],
    PURPLE
)

# ============================================
# FOOTER
# ============================================

draw.text(
    (70, 1240),
    "ЛОКАЛЬНЕ. КОРИСНЕ. НАШЕ.",
    fill=TEXT,
    font=h2_font
)

draw.text(
    (70, 1290),
    "poruch.bot",
    fill=SUBTEXT,
    font=medium_font
)

draw.text(
    (950, 1280),
    "v0.2",
    fill="#888888",
    font=small_font
)

# ============================================
# SAVE
# ============================================

img.save("status.png")

print("DONE")
