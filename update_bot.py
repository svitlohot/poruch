import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ============================================
# НАСТРОЙКИ
# ============================================

WIDTH = 1080
HEIGHT = 1350

BG     = "#F5F1E8"
CARD   = "#FFFDFC"
BORDER = "#D9D4CA"

TEXT    = "#0D4B3E"
SUBTEXT = "#4F7A6F"

GREEN  = "#DDF4D7"
RED    = "#F8D7D7"
YELLOW = "#F5E7B8"
BLUE   = "#DCE8F5"
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
        return {"usd": "—", "eur": "—"}


def get_power():
    def fetch_status(key):
        try:
            url = f"https://api.svitlobot.in.ua/status?channel_key={key}"
            text = requests.get(url, timeout=5).text
            if "світло є" in text.lower():
                return "Є"
            elif "світла немає" in text.lower():
                return "Немає"
            else:
                return "—"
        except Exception as e:
            print("Power fetch error:", e)
            return "—"

    key1 = os.environ.get("SVITLO_KEY1", "")
    key2 = os.environ.get("SVITLO_KEY2", "")

    s1 = fetch_status(key1) if key1 else "—"
    s2 = fetch_status(key2) if key2 else "—"

    print(f"Power: Хотянівка={s1}, ПБХ, Осещина, МР={s2}")
    return {"hotyanivka": s1, "vyshhorod": s2}


def get_air():
    try:
        url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=50.5486&longitude=30.4197&current=european_aqi"
        data = requests.get(url, timeout=5).json()
        aqi = int(data["current"]["european_aqi"])

        if aqi <= 20:   status = "Відмінно"
        elif aqi <= 40: status = "Добре"
        elif aqi <= 60: status = "Помірно"
        elif aqi <= 80: status = "Погано"
        else:           status = "Дуже погано"

        print(f"Air: AQI={aqi}, {status}")
        return {"aqi": aqi, "status": status, "location": "Хотянівка"}
    except Exception as e:
        print("Air error:", e)
        return {"aqi": "—", "status": "Помилка", "location": ""}


def get_fuel():
    return {"a95": "55.90", "station": "Авантаж 7"}


def get_alert():
    try:
        url = "https://siren.pp.ua/api/v3/alerts"
        data = requests.get(url, timeout=5).json()
        vyshhorod = next(
            (r for r in data if r.get("regionId") == "74"),
            None
        )
        active = vyshhorod and bool(vyshhorod.get("activeAlerts"))
        print(f"Alert: {'ТРИВОГА' if active else 'Тихо'}")
        return {"active": bool(active)}
    except Exception as e:
        print("Alert error:", e)
        return {"active": False}


def get_traffic():
    try:
        key = os.environ.get("GOOGLE_MAPS_KEY", "")
        url = (
            "https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins=50.59587618912401,30.56582047829475"
            f"&destinations=50.52299641605543,30.498424434465736"
            f"&mode=driving"
            f"&departure_time=now"
            f"&language=uk"
            f"&key={key}"
        )
        data = requests.get(url, timeout=5).json()
        element = data["rows"][0]["elements"][0]

        if element["status"] != "OK":
            return {"time": "—", "delay": "Немає даних"}

        duration = element["duration_in_traffic"]["value"] // 60
        duration_normal = element["duration"]["value"] // 60
        delay = duration - duration_normal

        if delay <= 2:
            delay_text = "Вільно"
        elif delay <= 10:
            delay_text = "Помірно"
        elif delay <= 20:
            delay_text = "Затори"
        else:
            delay_text = "Стоїмо"

        print(f"Traffic: {duration} хв, затримка {delay} хв")
        return {"time": f"{duration} хв", "delay": delay_text}

    except Exception as e:
        print("Traffic error:", e)
        return {"time": "—", "delay": "Помилка"}

# ============================================
# UI
# ============================================

img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

FONT_PATH = "Ubuntu-Bold.ttf"

try:
    title_font  = ImageFont.truetype(FONT_PATH, 76)
    h2_font     = ImageFont.truetype(FONT_PATH, 36)
    big_font    = ImageFont.truetype(FONT_PATH, 64)
    medium_font = ImageFont.truetype(FONT_PATH, 30)
    small_font  = ImageFont.truetype(FONT_PATH, 24)
except:
    title_font  = ImageFont.load_default()
    h2_font     = ImageFont.load_default()
    big_font    = ImageFont.load_default()
    medium_font = ImageFont.load_default()
    small_font  = ImageFont.load_default()

# ============================================
# HEADER
# ============================================

draw.text((70, 60),  "ПОРУЧ",                fill=TEXT,    font=title_font)
draw.text((70, 150), "СТАН ГРОМАДИ",         fill=TEXT,    font=h2_font)
draw.text((70, 205), "Хотянівка", fill=SUBTEXT, font=medium_font)

now = datetime.utcnow() + timedelta(hours=3)
draw.text((820, 70),  "Оновлено",               fill=SUBTEXT, font=small_font)
draw.text((820, 120), now.strftime("%d.%m.%Y"), fill=TEXT,    font=medium_font)
draw.text((820, 180), now.strftime("%H:%M"),    fill=TEXT,    font=big_font)

# ============================================
# CARD FUNCTIONS
# ============================================

def card(x, y, w, h, title, value, subtitle, color):
    draw.rounded_rectangle(
        [x, y, x+w, y+h], radius=34,
        fill=CARD, outline=BORDER, width=2
    )
    draw.ellipse([x+35, y+35, x+135, y+135], fill=color)
    draw.text((x+165, y+45),  title,    fill=TEXT,    font=h2_font)
    draw.text((x+165, y+105), value,    fill=TEXT,    font=big_font)
    draw.text((x+165, y+190), subtitle, fill=SUBTEXT, font=medium_font)


def dot_color(status):
    if status == "Є":     return "#4CAF50"
    if status == "Немає": return "#E53935"
    return "#9E9E9E"


def card_power(x, y, w, h, s1, s2, bg_color):
    draw.rounded_rectangle(
        [x, y, x+w, y+h], radius=34,
        fill=CARD, outline=BORDER, width=2
    )
    draw.ellipse([x+35, y+35, x+135, y+135], fill=bg_color)
    draw.text((x+165, y+35), "СВІТЛО", fill=TEXT, font=h2_font)

    draw.ellipse([x+165, y+98,  x+187, y+120], fill=dot_color(s1))
    draw.text(   (x+200, y+95),  f"Хотянівка: {s1}", fill=TEXT, font=medium_font)

    draw.ellipse([x+165, y+143, x+187, y+165], fill=dot_color(s2))
    draw.text((x+200, y+140), f"ПБХ/Осещина: {s2}",  fill=TEXT, font=medium_font)


def card_alert(x, y, w, h, active):
    bg_color   = RED        if active else GREEN
    dot        = "#E53935"  if active else "#4CAF50"
    value_text = "ТРИВОГА"  if active else "НЕМАЄ"
    sub_text   = "Увага"    if active else "Тихо"

    draw.rounded_rectangle(
        [x, y, x+w, y+h], radius=34,
        fill=CARD, outline=BORDER, width=2
    )
    draw.ellipse([x+35, y+35, x+135, y+135], fill=bg_color)
    draw.text((x+165, y+45),  "ТРИВОГА",  fill=TEXT,    font=h2_font)
    draw.text((x+165, y+105), value_text, fill=TEXT,    font=big_font)
    draw.ellipse([x+165, y+193, x+187, y+215], fill=dot)
    draw.text(   (x+200, y+190), sub_text, fill=SUBTEXT, font=medium_font)

# ============================================
# DATA
# ============================================

currency = get_currency()
fuel     = get_fuel()
air      = get_air()
alert    = get_alert()
power    = get_power()
traffic  = get_traffic()

# ============================================
# CARDS
# ============================================

LEFT   = 50
RIGHT  = 545
TOP    = 320
STEP   = 280
CARD_W = 485
CARD_H = 240

# 1. СВІТЛО
both_on     = power["hotyanivka"] == "Є" and power["vyshhorod"] == "Є"
power_color = GREEN if both_on else RED

card_power(
    LEFT, TOP, CARD_W, CARD_H,
    power["hotyanivka"],
    power["vyshhorod"],
    power_color
)

# 2. ТРИВОГА
card_alert(RIGHT, TOP, CARD_W, CARD_H, alert["active"])

# 3. КУРС ВАЛЮТ
card(
    LEFT, TOP + STEP, CARD_W, CARD_H,
    "КУРС",
    f"USD {currency['usd']}",
    f"EUR {currency['eur']}",
    BLUE
)

# 4. ПАЛИВО
card(
    RIGHT, TOP + STEP, CARD_W, CARD_H,
    "ПАЛИВО",
    f"A95 {fuel['a95']}",
    fuel["station"],
    YELLOW
)

# 5. ПОВІТРЯ
air_color = GREEN
if isinstance(air["aqi"], int):
    if air["aqi"] > 40: air_color = YELLOW
    if air["aqi"] > 80: air_color = RED

card(
    LEFT, TOP + STEP*2, CARD_W, CARD_H,
    f"ПОВІТРЯ · {air.get('location', '')}",
    f"AQI {air['aqi']}",
    air["status"],
    air_color
)

# 6. ДО КИЄВА
card(
    RIGHT, TOP + STEP*2, CARD_W, CARD_H,
    "ДО КИЄВА",
    traffic["time"],
    traffic["delay"],
    PURPLE
)

# ============================================
# FOOTER
# ============================================

draw.text((70, 1240),  "ЛОКАЛЬНЕ. КОРИСНЕ. НАШЕ.", fill=TEXT,      font=h2_font)
draw.text((70, 1290),  "poruch.bot",               fill=SUBTEXT,   font=medium_font)
draw.text((950, 1280), "v0.5",                     fill="#888888", font=small_font)

# ============================================
# SAVE
# ============================================

img.save("status.png")
print("DONE")
