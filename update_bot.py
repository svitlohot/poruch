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
        return {"usd": round(float(usd["sale"]), 2), "eur": round(float(eur["sale"]), 2)}
    except Exception as e:
        print("Currency error:", e)
        return {"usd": "—", "eur": "—"}

def get_power():
    def fetch_status(key):
        try:
            url = f"https://api.svitlobot.in.ua/status?channel_key={key}"
            text = requests.get(url, timeout=5).text
            if "світло є" in text.lower():   return "Є"
            elif "світла немає" in text.lower(): return "Немає"
            else: return "—"
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
    f_header  = ImageFont.truetype(FONT_PATH, 72)
    f_sub     = ImageFont.truetype(FONT_PATH, 38)
    f_loc     = ImageFont.truetype(FONT_PATH, 30)
    f_label   = ImageFont.truetype(FONT_PATH, 27)
    f_big     = ImageFont.truetype(FONT_PATH, 68)
    f_medium  = ImageFont.truetype(FONT_PATH, 36)
    f_small   = ImageFont.truetype(FONT_PATH, 26)
    f_tiny    = ImageFont.truetype(FONT_PATH, 22)
    f_footer  = ImageFont.truetype(FONT_PATH, 32)
except:
    f_header = f_sub = f_loc = f_label = f_big = f_medium = f_small = f_tiny = f_footer = ImageFont.load_default()

# ============================================
# CANVAS
# ============================================

img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

# ============================================
# ХЕДЕР (білий фон щоб логотип зливався)
# ============================================

draw.rectangle([0, 0, WIDTH, 250], fill=WHITE)

try:
    logo = Image.open("logo.png").convert("RGBA")
    logo = logo.resize((170, 170), Image.LANCZOS)
    img.paste(logo, (40, 38), logo)
    text_x = 230
except:
    text_x = 50

now = datetime.utcnow() + timedelta(hours=3)

draw.text((text_x, 42),  "СТАН ГРОМАДИ", fill=TEXT,    font=f_header)
draw.text((text_x, 128), "Хотянівка",    fill=SUBTEXT, font=f_sub)

draw.text((760, 42),  "Оновлено",               fill=SUBTEXT, font=f_tiny)
draw.text((760, 72),  now.strftime("%d.%m.%Y"), fill=TEXT,    font=f_small)
draw.text((760, 110), now.strftime("%H:%M"),    fill=TEXT,    font=f_big)

# Розділювач
draw.rectangle([0, 250, WIDTH, 253], fill=BORDER)

# ============================================
# ІКОНКИ (геометричні)
# ============================================

def icon_lightning(cx, cy, color):
    # блискавка зі смужок
    pts = [(cx, cy-28), (cx+14, cy-28), (cx-2, cy+2), (cx+10, cy+2), (cx-14, cy+28), (cx+2, cy+28), (cx, cy-28)]
    draw.polygon(pts, fill=color)

def icon_bell(cx, cy, color):
    # дзвін = напівкруг + прямокутник
    draw.ellipse([cx-22, cy-24, cx+22, cy+10], fill=color)
    draw.rectangle([cx-22, cy+2, cx+22, cy+14], fill=color)
    draw.ellipse([cx-8, cy+12, cx+8, cy+22], fill=color)

def icon_dollar(cx, cy, color):
    draw.ellipse([cx-22, cy-22, cx+22, cy+22], fill=color)
    draw.text((cx-8, cy-16), "$", fill=WHITE, font=f_medium)

def icon_fuel(cx, cy, color):
    draw.rectangle([cx-18, cy-22, cx+12, cy+22], fill=color)
    draw.rectangle([cx+8, cy-14, cx+22, cy+4], fill=color)
    draw.ellipse([cx+14, cy-18, cx+24, cy-8], fill=color)

def icon_wind(cx, cy, color):
    for i, y_off in enumerate([-10, 0, 10]):
        w = 30 if i == 1 else 20
        draw.rectangle([cx-w, cy+y_off-3, cx+w, cy+y_off+3], fill=color)
        draw.ellipse([cx+w-6, cy+y_off-6, cx+w+6, cy+y_off+6], fill=color)

def icon_car(cx, cy, color):
    draw.rectangle([cx-28, cy-6, cx+28, cy+14], fill=color)
    draw.rectangle([cx-18, cy-22, cx+18, cy-4], fill=color)
    draw.ellipse([cx-22, cy+8, cx-8, cy+22], fill=color)
    draw.ellipse([cx+8, cy+8, cx+22, cy+22], fill=color)

# ============================================
# КАРТКИ
# ============================================

L  = 38
R  = 558
TY = 270
S  = 285
CW = 494
CH = 262
PX = 140   # текст починається після іконки
PY = 22

def draw_card_base(x, y, w, h, theme):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=28, fill=theme["bg"], outline=BORDER, width=2)

def draw_dot(x, y, r, color):
    draw.ellipse([x-r, y-r, x+r, y+r], fill=color)

# ---- ІКОНКА + ПІДКЛАДКА ----
def card_icon_bg(x, y, theme, icon_fn):
    cx = x + 72
    cy = y + CH // 2
    draw.ellipse([cx-44, cy-44, cx+44, cy+44], fill=theme["accent"])
    icon_fn(cx, cy, WHITE)

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

if both_on:
    theme_p = C_GREEN
    power_summary = "Світло скрізь є"
elif any_on:
    theme_p = C_ORANGE
    power_summary = "Частково є"
else:
    theme_p = C_RED
    power_summary = "Світла немає"

draw_card_base(L, TY, CW, CH, theme_p)
card_icon_bg(L, TY, theme_p, icon_lightning)

draw.text((L+PX, TY+PY),    "СВІТЛО",       fill=theme_p["dark"], font=f_label)

dot1 = C_GREEN["accent"] if s1_on else C_RED["accent"]
draw_dot(L+PX, TY+80, 9, dot1)
draw.text((L+PX+18, TY+68), f"Хотянівка: {power['hotyanivka']}", fill=theme_p["dark"], font=f_medium)

dot2 = C_GREEN["accent"] if s2_on else C_RED["accent"]
draw_dot(L+PX, TY+128, 9, dot2)
draw.text((L+PX+18, TY+116), f"ПБХ/Осещина: {power['pbkh']}", fill=theme_p["dark"], font=f_medium)

draw.text((L+PX, TY+178), power_summary, fill=theme_p["accent"], font=f_small)

# ============================================
# 2. ТРИВОГА
# ============================================

theme_a = C_RED if alert["active"] else C_GREEN
draw_card_base(R, TY, CW, CH, theme_a)
card_icon_bg(R, TY, theme_a, icon_bell)

draw.text((R+PX, TY+PY),   "ТРИВОГА", fill=theme_a["dark"], font=f_label)
alert_val = "ТРИВОГА" if alert["active"] else "НЕМАЄ"
draw.text((R+PX, TY+65),   alert_val,  fill=theme_a["dark"], font=f_big)

dot_alert = C_RED["accent"] if alert["active"] else C_GREEN["accent"]
draw_dot(R+PX, TY+200, 9, dot_alert)
draw.text((R+PX+18, TY+190), "Вишгородський р-н", fill=theme_a["dark"], font=f_small)

# ============================================
# 3. КУРС ВАЛЮТ
# ============================================

draw_card_base(L, TY+S, CW, CH, C_BLUE)
card_icon_bg(L, TY+S, C_BLUE, icon_dollar)

draw.text((L+PX, TY+S+PY),   "КУРС ВАЛЮТ",           fill=C_BLUE["dark"],   font=f_label)
draw.text((L+PX, TY+S+62),   f"USD {currency['usd']}", fill=C_BLUE["dark"],   font=f_big)
draw.text((L+PX, TY+S+148),  f"EUR  {currency['eur']}", fill=C_BLUE["accent"], font=f_medium)
draw.text((L+PX, TY+S+198),  "Приватбанк, курс продажу", fill=C_BLUE["accent"], font=f_tiny)

# ============================================
# 4. ПАЛИВО
# ============================================

draw_card_base(R, TY+S, CW, CH, C_YELLOW)
card_icon_bg(R, TY+S, C_YELLOW, icon_fuel)

draw.text((R+PX, TY+S+PY),  "ПАЛИВО · " + fuel["station"], fill=C_YELLOW["dark"], font=f_label)
draw.text((R+PX, TY+S+58),  "А-95", fill=C_YELLOW["dark"],   font=f_medium)
draw.text((R+PX+120, TY+S+55), f"{fuel['a95']}", fill=C_YELLOW["accent"], font=f_big)
draw.text((R+PX, TY+S+138), f"Газ: {fuel['gas']}  Дизель: {fuel['diesel']}", fill=C_YELLOW["dark"], font=f_small)
draw.text((R+PX, TY+S+198), "грн/літр", fill=C_YELLOW["accent"], font=f_tiny)

# ============================================
# 5. ПОВІТРЯ
# ============================================

aqi_val = air["aqi"]
if isinstance(aqi_val, int):
    if aqi_val <= 40:   theme_air = C_GREEN
    elif aqi_val <= 80: theme_air = C_ORANGE
    else:               theme_air = C_RED
else:
    theme_air = C_TEAL

draw_card_base(L, TY+S*2, CW, CH, theme_air)
card_icon_bg(L, TY+S*2, theme_air, icon_wind)

draw.text((L+PX, TY+S*2+PY),   "ПОВІТРЯ · Хотянівка",  fill=theme_air["dark"],   font=f_label)
draw.text((L+PX, TY+S*2+62),   f"AQI {aqi_val}",       fill=theme_air["dark"],   font=f_big)
draw.text((L+PX, TY+S*2+148),  air["status"],           fill=theme_air["accent"], font=f_medium)
draw.text((L+PX, TY+S*2+198),  "European AQI",          fill=theme_air["accent"], font=f_tiny)

# ============================================
# 6. ДО КИЄВА
# ============================================

delay_themes = {"Вільно": C_GREEN, "Помірно": C_ORANGE, "Затори": C_RED, "Стоїмо": C_RED}
theme_t = delay_themes.get(traffic["delay"], C_PURPLE)

draw_card_base(R, TY+S*2, CW, CH, theme_t)
card_icon_bg(R, TY+S*2, theme_t, icon_car)

draw.text((R+PX, TY+S*2+PY),  "ДО КИЄВА · м. Героїв Дніпра", fill=theme_t["dark"],   font=f_label)
draw.text((R+PX, TY+S*2+62),  traffic["time"],                 fill=theme_t["dark"],   font=f_big)
draw.text((R+PX, TY+S*2+148), traffic["delay"],                fill=theme_t["accent"], font=f_big)
draw.text((R+PX, TY+S*2+218), "з урахуванням пробок",         fill=theme_t["accent"], font=f_tiny)

# ============================================
# ФУТЕР
# ============================================

fy = TY + S*3 + 15
draw.rectangle([38, fy, WIDTH-38, fy+2], fill=BORDER)
draw.text((50, fy+18), "Стан громади оновлюється кожні 10 хв", fill=SUBTEXT,   font=f_small)
draw.text((50, fy+55), "Поруч | Хотянівка  •  @poruch_ua_bot", fill=TEXT,      font=f_footer)
draw.text((970, fy+62), "v0.7", fill="#BBBBBB", font=f_tiny)

# ============================================
# SAVE
# ============================================

img.save("status.png")
print("DONE")
