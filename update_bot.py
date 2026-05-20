import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ============================================
# НАСТРОЙКИ
# ============================================

WIDTH  = 1080
HEIGHT = 1440

BG     = "#F5F1E8"
CARD   = "#FFFFFF"
BORDER = "#E0DDD6"

TEXT    = "#0D4B3E"
SUBTEXT = "#4F7A6F"
WHITE   = "#FFFFFF"

# Кольори карток
C_GREEN  = {"bg": "#E8F5E2", "accent": "#4CAF50", "dark": "#2E7D32"}
C_RED    = {"bg": "#FDECEA", "accent": "#E53935", "dark": "#B71C1C"}
C_BLUE   = {"bg": "#E3F0FB", "accent": "#1E88E5", "dark": "#1565C0"}
C_YELLOW = {"bg": "#FFF8E1", "accent": "#F9A825", "dark": "#E65100"}
C_PURPLE = {"bg": "#F3E5F5", "accent": "#8E24AA", "dark": "#6A1B9A"}
C_TEAL   = {"bg": "#E0F2F1", "accent": "#00897B", "dark": "#004D40"}

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

    print(f"Power: Хотянівка={s1}, ПБХ/Осещина={s2}")
    return {"hotyanivka": s1, "pbkh": s2}


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
        return {"aqi": aqi, "status": status}
    except Exception as e:
        print("Air error:", e)
        return {"aqi": "—", "status": "Помилка"}


def get_fuel():
    return {"a95": "55.90", "station": "Авантаж 7"}


def get_alert():
    try:
        url = "https://siren.pp.ua/api/v3/alerts"
        data = requests.get(url, timeout=5).json()
        vyshhorod = next((r for r in data if r.get("regionId") == "74"), None)
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
            f"&mode=driving&departure_time=now&language=uk&key={key}"
        )
        data = requests.get(url, timeout=5).json()
        element = data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            return {"time": "—", "delay": "Немає даних"}
        duration = element["duration_in_traffic"]["value"] // 60
        duration_normal = element["duration"]["value"] // 60
        delay = duration - duration_normal
        if delay <= 2:    delay_text = "Вільно"
        elif delay <= 10: delay_text = "Помірно"
        elif delay <= 20: delay_text = "Затори"
        else:             delay_text = "Стоїмо"
        print(f"Traffic: {duration} хв, {delay_text}")
        return {"time": f"{duration} хв", "delay": delay_text}
    except Exception as e:
        print("Traffic error:", e)
        return {"time": "—", "delay": "Помилка"}

# ============================================
# ШРИФТИ
# ============================================

FONT_PATH = "Ubuntu-Bold.ttf"
FONT_REG  = "Ubuntu-Bold.ttf"  # якщо є Regular — замінити

try:
    f_title  = ImageFont.truetype(FONT_PATH, 80)
    f_sub    = ImageFont.truetype(FONT_PATH, 32)
    f_label  = ImageFont.truetype(FONT_PATH, 26)
    f_big    = ImageFont.truetype(FONT_PATH, 62)
    f_medium = ImageFont.truetype(FONT_PATH, 30)
    f_small  = ImageFont.truetype(FONT_PATH, 22)
    f_tiny   = ImageFont.truetype(FONT_PATH, 20)
except:
    f_title = f_sub = f_label = f_big = f_medium = f_small = f_tiny = ImageFont.load_default()

# ============================================
# CANVAS
# ============================================

img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

# ============================================
# ХЕДЕР
# ============================================

# Логотип
try:
    logo = Image.open("logo.png").convert("RGBA")
    logo_size = 160
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    img.paste(logo, (50, 40), logo)
    text_x = 230
except:
    text_x = 70

draw.text((text_x, 48),  "ПОРУЧ",        fill=TEXT,    font=f_title)
draw.text((text_x, 138), "СТАН ГРОМАДИ", fill=TEXT,    font=f_sub)
draw.text((text_x, 178), "Хотянівка",    fill=SUBTEXT, font=f_label)

# Дата і час
now = datetime.utcnow() + timedelta(hours=3)
draw.text((780, 50),  "Оновлено",              fill=SUBTEXT, font=f_small)
draw.text((780, 80),  now.strftime("%d.%m.%Y"), fill=TEXT,    font=f_medium)
draw.text((780, 130), now.strftime("%H:%M"),    fill=TEXT,    font=f_big)

# Розділювач
draw.rectangle([50, 230, WIDTH-50, 233], fill=BORDER)

# ============================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================

def draw_card(x, y, w, h, theme):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=28, fill=theme["bg"], outline=BORDER, width=2)

def draw_dot(x, y, r, color):
    draw.ellipse([x-r, y-r, x+r, y+r], fill=color)

def label(x, y, text, color=None, font=None):
    draw.text((x, y), text, fill=color or SUBTEXT, font=font or f_label)

def big_text(x, y, text, color=None):
    draw.text((x, y), text, fill=color or TEXT, font=f_big)

def medium_text(x, y, text, color=None):
    draw.text((x, y), text, fill=color or TEXT, font=f_medium)

def small_text(x, y, text, color=None):
    draw.text((x, y), text, fill=color or SUBTEXT, font=f_small)

# ============================================
# ДАНІ
# ============================================

currency = get_currency()
fuel     = get_fuel()
air      = get_air()
alert    = get_alert()
power    = get_power()
traffic  = get_traffic()

# ============================================
# СІТКА КАРТОК
# ============================================

L  = 40       # лівий відступ
R  = 560      # права колонка
TY = 260      # перший рядок
S  = 290      # крок по вертикалі
CW = 490      # ширина картки
CH = 255      # висота картки
PX = 30       # внутрішній відступ зліва (від картки)
PY = 22       # внутрішній відступ зверху

# ============================================
# 1. СВІТЛО
# ============================================

p = power
s1_on = p["hotyanivka"] == "Є"
s2_on = p["pbkh"] == "Є"
both_on = s1_on and s2_on
theme = C_GREEN if both_on else C_RED

draw_card(L, TY, CW, CH, theme)
label(L+PX, TY+PY, "СВІТЛО", theme["dark"], f_label)

# рядок 1
dot1 = C_GREEN["accent"] if s1_on else (C_RED["accent"] if p["hotyanivka"] == "Немає" else "#9E9E9E")
draw_dot(L+PX+10, TY+85, 10, dot1)
medium_text(L+PX+30, TY+72, f"Хотянівка: {p['hotyanivka']}", theme["dark"])

# рядок 2
dot2 = C_GREEN["accent"] if s2_on else (C_RED["accent"] if p["pbkh"] == "Немає" else "#9E9E9E")
draw_dot(L+PX+10, TY+130, 10, dot2)
medium_text(L+PX+30, TY+117, f"ПБХ/Осещина: {p['pbkh']}", theme["dark"])

# статус загальний
status_power = "Світло є" if both_on else ("Перевірте" if s1_on or s2_on else "Відключено")
small_text(L+PX, TY+175, status_power, theme["accent"])

# ============================================
# 2. ТРИВОГА
# ============================================

theme_a = C_RED if alert["active"] else C_GREEN
draw_card(R, TY, CW, CH, theme_a)
label(R+PX, TY+PY, "ТРИВОГА", theme_a["dark"], f_label)

alert_val = "ТРИВОГА" if alert["active"] else "НЕМАЄ"
big_text(R+PX, TY+65, alert_val, theme_a["dark"])

dot_a = C_RED["accent"] if alert["active"] else C_GREEN["accent"]
sub_a = "Вишгородський р-н" if alert["active"] else "Вишгородський р-н"
draw_dot(R+PX+10, TY+185, 10, dot_a)
small_text(R+PX+28, TY+177, sub_a, theme_a["dark"])

# ============================================
# 3. КУРС ВАЛЮТ
# ============================================

draw_card(L, TY+S, CW, CH, C_BLUE)
label(L+PX, TY+S+PY, "КУРС ВАЛЮТ", C_BLUE["dark"], f_label)
big_text(L+PX, TY+S+62, f"USD {currency['usd']}", C_BLUE["dark"])
medium_text(L+PX, TY+S+142, f"EUR  {currency['eur']}", C_BLUE["accent"])
small_text(L+PX, TY+S+190, "Приватбанк, курс продажу", C_BLUE["accent"])

# ============================================
# 4. ПАЛИВО
# ============================================

draw_card(R, TY+S, CW, CH, C_YELLOW)
label(R+PX, TY+S+PY, "ПАЛИВО", C_YELLOW["dark"], f_label)
small_text(R+PX, TY+S+55, fuel["station"], C_YELLOW["dark"])
big_text(R+PX, TY+S+85, f"А-95", C_YELLOW["dark"])
big_text(R+PX+200, TY+S+85, f"{fuel['a95']}", C_YELLOW["accent"])
small_text(R+PX, TY+S+175, "грн/літр", C_YELLOW["accent"])

# ============================================
# 5. ПОВІТРЯ
# ============================================

aqi_val = air["aqi"]
if isinstance(aqi_val, int):
    if aqi_val <= 40:   theme_air = C_GREEN
    elif aqi_val <= 80: theme_air = C_YELLOW
    else:               theme_air = C_RED
else:
    theme_air = C_TEAL

draw_card(L, TY+S*2, CW, CH, theme_air)
label(L+PX, TY+S*2+PY, "ПОВІТРЯ · Хотянівка", theme_air["dark"], f_label)
big_text(L+PX, TY+S*2+62, f"AQI {aqi_val}", theme_air["dark"])
medium_text(L+PX, TY+S*2+145, air["status"], theme_air["accent"])
small_text(L+PX, TY+S*2+190, "European Air Quality Index", theme_air["accent"])

# ============================================
# 6. ДО КИЄВА
# ============================================

delay_colors = {
    "Вільно":  C_GREEN,
    "Помірно": C_YELLOW,
    "Затори":  C_YELLOW,
    "Стоїмо":  C_RED,
}
theme_t = delay_colors.get(traffic["delay"], C_PURPLE)

draw_card(R, TY+S*2, CW, CH, theme_t)
label(R+PX, TY+S*2+PY, "ДО КИЄВА · м. Героїв Дніпра", theme_t["dark"], f_label)
big_text(R+PX, TY+S*2+62, traffic["time"], theme_t["dark"])
medium_text(R+PX, TY+S*2+145, traffic["delay"], theme_t["accent"])
small_text(R+PX, TY+S*2+190, "з урахуванням пробок", theme_t["accent"])

# ============================================
# ФУТЕР
# ============================================

fy = TY + S*3 + 20
draw.rectangle([50, fy, WIDTH-50, fy+2], fill=BORDER)

draw.text((50, fy+20), "Стан громади оновлюється кожні 10 хв", fill=SUBTEXT, font=f_small)
draw.text((50, fy+50), "@poruch_ua_bot", fill=TEXT, font=f_sub)
draw.text((950, fy+55), "v0.6", fill="#BBBBBB", font=f_tiny)

# ============================================
# SAVE
# ============================================

img.save("status.png")
print("DONE")
