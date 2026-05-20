import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ============================================
# НАСТРОЙКИ
# ============================================

WIDTH  = 1080
HEIGHT = 1440

BG      = "#F5F1E8"
WHITE   = "#FFFFFF"
BORDER  = "#E0DDD6"
TEXT    = "#0D4B3E"
SUBTEXT = "#4F7A6F"

C_GREEN  = {"bg": "#E8F5E2", "accent": "#4CAF50", "dark": "#2E7D32"}
C_RED    = {"bg": "#FDECEA", "accent": "#E53935", "dark": "#B71C1C"}
C_ORANGE = {"bg": "#FFF3E0", "accent": "#FB8C00", "dark": "#E65100"}
C_BLUE   = {"bg": "#E3F0FB", "accent": "#1E88E5", "dark": "#1565C0"}
C_YELLOW = {"bg": "#FFF8E1", "accent": "#F9A825", "dark": "#F57F17"}
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
        return {"usd": round(float(usd["sale"]), 2), "eur": round(float(eur["sale"]), 2)}
    except Exception as e:
        print("Currency error:", e)
        return {"usd": "—", "eur": "—"}

def get_power():
    def fetch_status(key):
        try:
            url = f"https://api.svitlobot.in.ua/status?channel_key={key}"
            text = requests.get(url, timeout=5).text
            if "світло є" in text.lower():      return "Є"
            elif "світла немає" in text.lower(): return "Немає"
            else:                                return "—"
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
        key = os.environ.get("GOOGLE_MAPS_KEY", "")
        url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        payload = {
            "location": {"latitude": 50.5486, "longitude": 30.4197},
            "languageCode": "uk"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{url}?key={key}",
            json=payload,
            headers=headers,
            timeout=5
        )
        data = response.json()

        # Беремо Universal AQI
        aqi_info = next(
            (i for i in data.get("indexes", []) if i.get("code") == "uaqi"),
            None
        )
        if not aqi_info:
            raise ValueError("No AQI data")

        aqi = aqi_info.get("aqiDisplay", "—")
        category = aqi_info.get("category", "")

        # Перекладаємо категорію
        translations = {
            "Excellent air quality": "Відмінно",
            "Good air quality": "Добре",
            "Moderate air quality": "Помірно",
            "Low air quality": "Погано",
            "Poor air quality": "Дуже погано",
            "Hazardous air quality": "Небезпечно",
        }
        status = translations.get(category, category)

        print(f"Air: AQI={aqi}, {status}")
        return {"aqi": aqi, "status": status}

    except Exception as e:
        print("Air error:", e)
        return {"aqi": "—", "status": "Помилка"}

def get_fuel():
    return {"a95": "55.90", "gas": "—", "diesel": "—", "station": "Авантаж 7"}

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
try:
    f_header = ImageFont.truetype(FONT_PATH, 72)
    f_sub    = ImageFont.truetype(FONT_PATH, 36)
    f_label  = ImageFont.truetype(FONT_PATH, 26)
    f_big    = ImageFont.truetype(FONT_PATH, 68)
    f_medium = ImageFont.truetype(FONT_PATH, 36)
    f_small  = ImageFont.truetype(FONT_PATH, 24)
    f_tiny   = ImageFont.truetype(FONT_PATH, 20)
    f_footer = ImageFont.truetype(FONT_PATH, 32)
    f_time   = ImageFont.truetype(FONT_PATH, 64)
except:
    f_header = f_sub = f_label = f_big = f_medium = f_small = f_tiny = f_footer = f_time = ImageFont.load_default()

# ============================================
# CANVAS
# ============================================

img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

# ============================================
# ХЕДЕР — чітко розділений на ліву і праву зони
# ============================================

HEADER_H = 230
draw.rectangle([0, 0, WIDTH, HEADER_H], fill=WHITE)

# Ліва зона: логотип (40..220) + текст (230..640)
# Права зона: дата+час (650..1040)

try:
    logo = Image.open("logo.png").convert("RGBA")
    logo = logo.resize((170, 170), Image.LANCZOS)
    img.paste(logo, (40, 30), logo)
    tx = 230
except:
    tx = 50

now = datetime.utcnow() + timedelta(hours=3)

draw.text((tx, 30),  "СТАН ГРОМАДИ", fill=TEXT,    font=f_header)
draw.text((tx, 118), "Хотянівка",    fill=SUBTEXT, font=f_sub)

# Дата і час — права зона, вирівняно по правому краю
draw.text((820, 30),  "Оновлено",               fill=SUBTEXT, font=f_tiny)
draw.text((820, 58),  now.strftime("%d.%m.%Y"), fill=TEXT,    font=f_small)
draw.text((820, 95),  now.strftime("%H:%M"),    fill=TEXT,    font=f_time)

draw.rectangle([0, HEADER_H, WIDTH, HEADER_H+3], fill=BORDER)

# ============================================
# СІТКА КАРТОК
# ============================================

L   = 38
R   = 558
TY  = HEADER_H + 22
S   = 286
CW  = 482
CH  = 258
PX  = 26
PY  = 18

def draw_card(x, y, theme):
    draw.rounded_rectangle([x, y, x+CW, y+CH], radius=28, fill=theme["bg"], outline=BORDER, width=2)

def draw_dot(x, y, color):
    draw.ellipse([x-10, y-10, x+10, y+10], fill=color)

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
# 1. СВІТЛО
# ============================================

s1_on   = power["hotyanivka"] == "Є"
s2_on   = power["pbkh"] == "Є"
both_on = s1_on and s2_on
any_on  = s1_on or s2_on

if both_on:    tp = C_GREEN;  power_summary = "Світло скрізь є"
elif any_on:   tp = C_ORANGE; power_summary = "Частково є"
else:          tp = C_RED;    power_summary = "Світла немає"

draw_card(L, TY, tp)
draw.text((L+PX, TY+PY), "СВІТЛО", fill=tp["dark"], font=f_label)

draw_dot(L+PX+10, TY+82, C_GREEN["accent"] if s1_on else C_RED["accent"])
draw.text((L+PX+28, TY+70), f"Хотянівка: {power['hotyanivka']}", fill=tp["dark"], font=f_medium)

draw_dot(L+PX+10, TY+130, C_GREEN["accent"] if s2_on else C_RED["accent"])
draw.text((L+PX+28, TY+118), f"ПБХ/Осещина: {power['pbkh']}", fill=tp["dark"], font=f_medium)

draw.text((L+PX, TY+192), power_summary, fill=tp["accent"], font=f_small)

# ============================================
# 2. ТРИВОГА
# ============================================

ta = C_RED if alert["active"] else C_GREEN
draw_card(R, TY, ta)
draw.text((R+PX, TY+PY), "ТРИВОГА", fill=ta["dark"], font=f_label)

draw.text((R+PX, TY+58), "ТРИВОГА" if alert["active"] else "НЕМАЄ", fill=ta["dark"], font=f_big)

draw_dot(R+PX+10, TY+205, C_RED["accent"] if alert["active"] else C_GREEN["accent"])
draw.text((R+PX+28, TY+193), "Вишгородський р-н", fill=ta["dark"], font=f_small)

# ============================================
# 3. КУРС ВАЛЮТ
# ============================================

draw_card(L, TY+S, C_BLUE)
draw.text((L+PX, TY+S+PY),  "КУРС ВАЛЮТ",              fill=C_BLUE["dark"],   font=f_label)
draw.text((L+PX, TY+S+58),  f"USD {currency['usd']}",  fill=C_BLUE["dark"],   font=f_big)
draw.text((L+PX, TY+S+145), f"EUR  {currency['eur']}", fill=C_BLUE["accent"], font=f_medium)
draw.text((L+PX, TY+S+200), "Приватбанк, курс продажу", fill=C_BLUE["accent"], font=f_tiny)

# ============================================
# 4. ПАЛИВО — всі значення одним шрифтом f_big
# ============================================

draw_card(R, TY+S, C_YELLOW)
draw.text((R+PX, TY+S+PY),  f"ПАЛИВО · {fuel['station']}", fill=C_YELLOW["dark"],   font=f_label)
draw.text((R+PX, TY+S+58),  f"А-95  {fuel['a95']}",        fill=C_YELLOW["dark"],   font=f_big)
draw.text((R+PX, TY+S+145), f"Газ: {fuel['gas']}   Диз: {fuel['diesel']}", fill=C_YELLOW["dark"], font=f_medium)
draw.text((R+PX, TY+S+200), "грн/літр",                     fill=C_YELLOW["accent"], font=f_tiny)

# ============================================
# 5. ПОВІТРЯ
# ============================================

aqi_val = air["aqi"]
if isinstance(aqi_val, int):
    if aqi_val <= 40:   ta_air = C_GREEN
    elif aqi_val <= 80: ta_air = C_ORANGE
    else:               ta_air = C_RED
else:
    ta_air = C_TEAL

draw_card(L, TY+S*2, ta_air)
draw.text((L+PX, TY+S*2+PY),  "ПОВІТРЯ · Хотянівка", fill=ta_air["dark"],   font=f_label)
draw.text((L+PX, TY+S*2+58),  f"AQI {aqi_val}",      fill=ta_air["dark"],   font=f_big)
draw.text((L+PX, TY+S*2+145), air["status"],          fill=ta_air["accent"], font=f_medium)
draw.text((L+PX, TY+S*2+200), "European AQI",         fill=ta_air["accent"], font=f_tiny)

# ============================================
# 6. ДО КИЄВА
# ============================================

delay_themes = {"Вільно": C_GREEN, "Помірно": C_ORANGE, "Затори": C_RED, "Стоїмо": C_RED}
tt = delay_themes.get(traffic["delay"], C_TEAL)

draw_card(R, TY+S*2, tt)
draw.text((R+PX, TY+S*2+PY),  "ДО КИЄВА · м. Героїв Дніпра", fill=tt["dark"],   font=f_label)
draw.text((R+PX, TY+S*2+58),  traffic["time"],                 fill=tt["dark"],   font=f_big)
draw.text((R+PX, TY+S*2+145), traffic["delay"],                fill=tt["accent"], font=f_medium)
draw.text((R+PX, TY+S*2+200), "з урахуванням пробок",         fill=tt["accent"], font=f_tiny)

# ============================================
# ФУТЕР
# ============================================

fy = TY + S*3 + 16
draw.rectangle([38, fy, WIDTH-38, fy+2], fill=BORDER)
draw.text((50, fy+14), "Стан громади оновлюється кожні 10 хв",  fill=SUBTEXT, font=f_footer)
draw.text((50, fy+58), "Поруч | Хотянівка  •  @poruch_ua_bot", fill=TEXT,    font=f_footer)
draw.text((960, fy+64), "v0.9", fill="#BBBBBB", font=f_small)

# ============================================
# SAVE
# ============================================

img.save("status.png")
print("DONE")
