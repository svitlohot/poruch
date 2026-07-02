import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ============================================
# НАСТРОЙКИ
# ============================================

WIDTH  = 1080
HEIGHT = 1620  # збільшили для блоку дороги

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
        return {
            "usd_buy":  round(float(usd["buy"]),  2),
            "usd_sale": round(float(usd["sale"]), 2),
            "eur_buy":  round(float(eur["buy"]),  2),
            "eur_sale": round(float(eur["sale"]), 2),
        }
    except Exception as e:
        print("Currency error:", e)
        return {"usd_buy": "—", "usd_sale": "—", "eur_buy": "—", "eur_sale": "—"}


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
    print(f"Power: Хотянівка={s1}, ПБХ/Центр={s2}")
    return {"hotyanivka": s1, "pbkh": s2}


def get_air():
    try:
        url = "https://www.saveecobot.com/station/24765.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        data = requests.get(url, headers=headers, timeout=10).json()

        aqi = int(data["aqi"])

        if aqi <= 50:    status = "Добра якість"
        elif aqi <= 100: status = "Помірна якість"
        elif aqi <= 150: status = "Шкідливо для чутливих"
        elif aqi <= 200: status = "Шкідливий рівень"
        elif aqi <= 300: status = "Дуже шкідливо"
        else:            status = "Небезпечно"

        print(f"Air (SaveEcoBot): AQI={aqi}, {status}")
        return {"aqi": aqi, "status": status}

    except Exception as e:
        print("Air error:", e)
        return {"aqi": "—", "status": "Помилка"}

def get_fuel():
    try:
        from bs4 import BeautifulSoup
        url = "https://index.minfin.com.ua/ua/markets/fuel/reg/kievskaya/"
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("a", string="Авантаж 7")
        if row:
            cells = row.find_parent("tr").find_all("td")
            print("Fuel cells:", [c.text.strip() for c in cells])
            a95    = cells[3].text.strip() if len(cells) > 3 else "—"
            diesel = cells[5].text.strip() if len(cells) > 5 else "—"
            gas    = cells[6].text.strip() if len(cells) > 6 else "—"
        else:
            a95 = diesel = gas = "—"
        print(f"Fuel: A95={a95}, Diesel={diesel}, Gas={gas}")
        return {"a95": a95, "diesel": diesel, "gas": gas, "station": "Авантаж 7"}
    except Exception as e:
        print("Fuel error:", e)
        return {"a95": "—", "diesel": "—", "gas": "—", "station": "Авантаж 7"}


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
            f"&mode=driving&language=uk&key={key}"
        )
        data = requests.get(url, timeout=5).json()
        element = data["rows"][0]["elements"][0]

        if element["status"] != "OK":
            return {"time": "—", "delay": "Немає даних"}

        duration = element["duration"]["value"] // 60

        print(f"Traffic: {duration} хв")
        return {"time": f"{duration} хв", "delay": "без пробок"}

    except Exception as e:
        print("Traffic error:", e)
        return {"time": "—", "delay": "Помилка"}


def get_weather():
    """Погода + попередження від УкрГМЦ для Київської обл."""
    try:
        # Поточна погода через Open-Meteo
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=50.5486&longitude=30.4197"
            "&current=temperature_2m,weathercode,windspeed_10m"
            "&windspeed_unit=ms"
        )
        data = requests.get(url, timeout=5).json()
        temp = round(data["current"]["temperature_2m"])
        code = data["current"]["weathercode"]
        wind = round(data["current"]["windspeed_10m"])

        # WMO weather code -> опис
        def wmo_desc(c):
            if c == 0:            return "Ясно"
            elif c <= 2:          return "Малохмарно"
            elif c == 3:          return "Хмарно"
            elif c <= 49:         return "Туман"
            elif c <= 57:         return "Мряка"
            elif c <= 67:         return "Дощ"
            elif c <= 77:         return "Сніг"
            elif c <= 82:         return "Злива"
            elif c <= 99:         return "Гроза"
            return "—"

        desc = wmo_desc(code)
        print(f"Weather: {temp}°, {desc}, вітер {wind} м/с")

        # Попередження від УкрГМЦ
        warning = None
        warning_level = None
        try:
            from bs4 import BeautifulSoup
            w_url = "https://www.meteo.gov.ua/ua/Meteorolohichni-poperedzhennya"
            html = requests.get(w_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")

            # Шукаємо всі h5 з попередженнями
            headers_h5 = soup.find_all("h5")
            for h in headers_h5:
                text = h.text.strip()
                keywords = ["Київськ", "всі област", "по всій", "центральних", "Україні"]
                if any(k in text for k in keywords):
                    warning = text
                    # Визначаємо рівень
                    if "III рівень" in text or "червоний" in text:
                        warning_level = "III"
                    elif "II рівень" in text or "оранжевий" in text:
                        warning_level = "II"
                    elif "I рівень" in text or "жовтий" in text:
                        warning_level = "I"
                    break
            print(f"Warning: {warning_level} - {warning[:60] if warning else 'немає'}")
        except Exception as e:
            print("Warning parse error:", e)

        return {
            "temp": temp,
            "desc": desc,
            "wind": wind,
            "warning": warning,
            "warning_level": warning_level,
        }

    except Exception as e:
        print("Weather error:", e)
        return {"temp": "—", "desc": "Помилка", "wind": 0, "warning": None, "warning_level": None}


# ============================================
# ШРИФТИ
# ============================================

FONT_PATH  = "Ubuntu-Bold.ttf"
EMOJI_PATH = "NotoEmoji-Bold.ttf"

try:
    f_header = ImageFont.truetype(FONT_PATH, 72)
    f_sub    = ImageFont.truetype(FONT_PATH, 36)
    f_label  = ImageFont.truetype(FONT_PATH, 26)
    f_big    = ImageFont.truetype(FONT_PATH, 56)
    f_medium = ImageFont.truetype(FONT_PATH, 36)
    f_small  = ImageFont.truetype(FONT_PATH, 24)
    f_tiny   = ImageFont.truetype(FONT_PATH, 20)
    f_footer = ImageFont.truetype(FONT_PATH, 32)
    f_time   = ImageFont.truetype(FONT_PATH, 64)
except:
    f_header = f_sub = f_label = f_big = f_medium = f_small = f_tiny = f_footer = f_time = ImageFont.load_default()

try:
    f_emoji_label = ImageFont.truetype(EMOJI_PATH, 24)
    f_emoji_big   = ImageFont.truetype(EMOJI_PATH, 48)
    has_emoji = True
except:
    has_emoji = False
    print("Emoji font not found, using text labels")

# ============================================
# CANVAS
# ============================================

img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(img)

# ============================================
# ХЕДЕР
# ============================================

HEADER_H = 230
draw.rectangle([0, 0, WIDTH, HEADER_H], fill=WHITE)

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

draw.text((820, 30),  "Оновлено",               fill=SUBTEXT, font=f_tiny)
draw.text((820, 58),  now.strftime("%d.%m.%Y"), fill=TEXT,    font=f_small)
draw.text((820, 95),  now.strftime("%H:%M"),    fill=TEXT,    font=f_time)

draw.rectangle([0, HEADER_H, WIDTH, HEADER_H+3], fill=BORDER)

# ============================================
# СІТКА
# ============================================

L   = 38
R   = 558
TY  = HEADER_H + 22
S   = 286       # крок між рядками карток
CW  = 482       # ширина малої картки
CH  = 258       # висота малої картки
PX  = 26
PY  = 18

def draw_card(x, y, w, h, theme):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=28, fill=theme["bg"], outline=BORDER, width=2)

def draw_dot(x, y, color):
    draw.ellipse([x-10, y-10, x+10, y+10], fill=color)

def label(x, y, text, color, font=None):
    draw.text((x, y), text, fill=color, font=font or f_label)

def label_with_emoji(x, y, emoji, text, color):
    if has_emoji:
        draw.text((x, y), emoji, font=f_emoji_label, fill=color)
        ex = x + int(draw.textlength(emoji, font=f_emoji_label)) + 8
    else:
        ex = x
    draw.text((ex, y), text, fill=color, font=f_label)

def t_big(x, y, text, color):
    draw.text((x, y), text, fill=color, font=f_big)

def t_med(x, y, text, color):
    draw.text((x, y), text, fill=color, font=f_medium)

def t_small(x, y, text, color):
    draw.text((x, y), text, fill=color, font=f_small)

# ============================================
# ДАНІ
# ============================================

currency = get_currency()
fuel     = get_fuel()
air      = get_air()
alert    = get_alert()
power    = get_power()
traffic  = get_traffic()
weather  = get_weather()

# ============================================
# 1. СВІТЛО
# ============================================

s1_on   = power["hotyanivka"] == "Є"
s2_on   = power["pbkh"] == "Є"
both_on = s1_on and s2_on
any_on  = s1_on or s2_on

if both_on:    tp = C_GREEN;  power_summary = "Світло є (не враховуючи локальні аварії)"
elif any_on:   tp = C_ORANGE; power_summary = "Частково є"
else:          tp = C_RED;    power_summary = "Світла немає"

draw_card(L, TY, CW, CH, tp)
label_with_emoji(L+PX, TY+PY, "⚡️", "СВІТЛО", tp["dark"])

draw_dot(L+PX+10, TY+82, C_GREEN["accent"] if s1_on else C_RED["accent"])
t_med(L+PX+28, TY+70, f"Хотянівка (СТ): {power['hotyanivka']}", tp["dark"])

draw_dot(L+PX+10, TY+130, C_GREEN["accent"] if s2_on else C_RED["accent"])
t_med(L+PX+28, TY+118, f"ПБХ/Центр: {power['pbkh']}", tp["dark"])

t_small(L+PX, TY+192, power_summary, tp["accent"])

# ============================================
# 2. ТРИВОГА
# ============================================

ta = C_RED if alert["active"] else C_GREEN
draw_card(R, TY, CW, CH, ta)
label_with_emoji(R+PX, TY+PY, "🚨", "ТРИВОГА", ta["dark"])
t_big(R+PX, TY+58, "ТРИВОГА" if alert["active"] else "НЕМАЄ", ta["dark"])
draw_dot(R+PX+10, TY+205, C_RED["accent"] if alert["active"] else C_GREEN["accent"])
t_small(R+PX+28, TY+193, "Вишгородський р-н", ta["dark"])

# ============================================
# 3. КУРС ВАЛЮТ
# ============================================

draw_card(L, TY+S, CW, CH, C_BLUE)
label_with_emoji(L+PX, TY+S+PY, "💵", "КУРС ВАЛЮТ", C_BLUE["dark"])
t_big(L+PX, TY+S+58,  f"USD {currency['usd_buy']} / {currency['usd_sale']}", C_BLUE["dark"])
t_med(L+PX, TY+S+145, f"EUR {currency['eur_buy']} / {currency['eur_sale']}", C_BLUE["accent"])
t_small(L+PX, TY+S+200, "купівля / продаж", C_BLUE["accent"])

# ============================================
# 4. ПАЛИВО
# ============================================

draw_card(R, TY+S, CW, CH, C_YELLOW)
label_with_emoji(R+PX, TY+S+PY, "⛽", f"ПАЛИВО · {fuel['station']}", C_YELLOW["dark"])
t_big(R+PX, TY+S+58,  f"А-95  {fuel['a95']}", C_YELLOW["dark"])
t_med(R+PX, TY+S+145, f"Газ: {fuel['gas']}   Диз: {fuel['diesel']}", C_YELLOW["dark"])
t_med(R+PX, TY+S+200, "грн/літр", C_YELLOW["accent"])

# ============================================
# 5. ЯКІСТЬ ПОВІТРЯ
# ============================================

aqi_val = air["aqi"]
if isinstance(aqi_val, int):
    if aqi_val <= 40:   ta_air = C_GREEN
    elif aqi_val <= 80: ta_air = C_ORANGE
    else:               ta_air = C_RED
else:
    ta_air = C_TEAL

draw_card(L, TY+S*2, CW, CH, ta_air)
label_with_emoji(L+PX, TY+S*2+PY, "🌿", "ЯКІСТЬ ПОВІТРЯ · Дані: SaveEcoBot", ta_air["dark"])
t_big(L+PX, TY+S*2+58,  f"AQI {aqi_val}", ta_air["dark"])
t_med(L+PX, TY+S*2+145, air["status"],    ta_air["accent"])

# ============================================
# 6. ПОГОДА / ПОПЕРЕДЖЕННЯ
# ============================================
w = weather
if w["warning"] and w["warning_level"]:
    import re

    warn_text = w["warning"]

    # Витягуємо дату з оригінального тексту
    date_match = re.search(r'(\d{1,2}\s+\w+)', warn_text)
    if date_match:
        parts = date_match.group(1).split()
        months = {"січня":"01","лютого":"02","березня":"03","квітня":"04",
                  "травня":"05","червня":"06","липня":"07","серпня":"08",
                  "вересня":"09","жовтня":"10","листопада":"11","грудня":"12"}
        m = months.get(parts[1], "??") if len(parts) == 2 else "??"
        date_str = f"· {parts[0]}.{m}."
    else:
        date_str = ""

    # Витягуємо тільки явище після "областях" або "районах"
    for keyword in ["областях ", "районах "]:
        idx = warn_text.rfind(keyword)
        if idx != -1:
            warn_text = warn_text[idx + len(keyword):]
            break

    # Видаляємо дужки з рівнем небезпечності
    warn_text = re.sub(r'\([^)]*рівень[^)]*\)', '', warn_text).strip().rstrip(".")

    # Розбиваємо по словах на рядки до 38 символів
    words = warn_text.split()
    lines = []
    current = ""
    for word in words:
        if len((current + " " + word).strip()) <= 38:
            current = (current + " " + word).strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    level_colors = {"I": C_YELLOW, "II": C_ORANGE, "III": C_RED}
    tw = level_colors.get(w["warning_level"], C_YELLOW)

    draw_card(R, TY+S*2, CW, CH, tw)
    label_with_emoji(R+PX, TY+S*2+PY, "⛈", f"ПОПЕРЕДЖЕННЯ · {w['warning_level']} рівень {date_str}", tw["dark"])

    for i, line in enumerate(lines[:3]):
        t_small(R+PX, TY+S*2+58 + i*34, line, tw["dark"])

    if w["wind"] > 0:
        t_med(R+PX, TY+S*2+175, f"Вітер {w['wind']} м/с", tw["dark"])

else:
    # Звичайна погода
    draw_card(R, TY+S*2, CW, CH, C_TEAL)
    label_with_emoji(R+PX, TY+S*2+PY, "🌤", "ПОГОДА · Хотянівка", C_TEAL["dark"])
    t_big(R+PX, TY+S*2+58,  f"+{w['temp']}°", C_TEAL["dark"])
    t_med(R+PX, TY+S*2+145, w["desc"],         C_TEAL["accent"])
    if w["wind"] > 0:
        t_small(R+PX, TY+S*2+198, f"Вітер {w['wind']} м/с", C_TEAL["accent"])

# ============================================
# 7. ДОРОГА — повна ширина
# ============================================

ROAD_Y  = TY + S*3
ROAD_H  = 280
ROAD_W  = WIDTH - L*2

t = traffic

if t["time"] == "—":
    tr_theme = C_TEAL
else:
    tr_theme = C_GREEN

draw_card(L, ROAD_Y, ROAD_W, ROAD_H, tr_theme)
label(L+PX, ROAD_Y+PY, "ДОРОГА · м. Героїв Дніпра", tr_theme["dark"])

t_big(L+PX, ROAD_Y+62,  t["time"],  tr_theme["dark"])
t_med(L+PX, ROAD_Y+150, t["delay"], tr_theme["accent"])
t_small(L+PX, ROAD_Y+205, "розрахунковий час без пробок", tr_theme["accent"])

# ============================================
# ФУТЕР
# ============================================

fy = ROAD_Y + ROAD_H + 20
draw.rectangle([38, fy, WIDTH-38, fy+2], fill=BORDER)
t_small(50, fy+14, "Дані оновлюються кожні 10 хв", SUBTEXT)
draw.text((50, fy+48), "Поруч | Хотянівка  •  @poruch_ua_bot", fill=TEXT, font=f_footer)
draw.text((960, fy+54), "v1.0", fill="#BBBBBB", font=f_tiny)

# ============================================
# SAVE
# ============================================

img.save("status.png", optimize=True, compress_level=9)
print("DONE")
