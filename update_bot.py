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
    print(f"Power: Хотянівка={s1}, ПБХ/Осещина={s2}")
    return {"hotyanivka": s1, "pbkh": s2}


def get_air():
    try:
        url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=50.5486&longitude=30.4197&current=european_aqi"
        data = requests.get(url, timeout=5).json()
        aqi = int(data["current"]["european_aqi"])
        if aqi <= 20:   status = "Чудова якість"
        elif aqi <= 40: status = "Хороша якість"
        elif aqi <= 60: status = "Помірна якість"
        elif aqi <= 80: status = "Погана якість"
        else:           status = "Небезпечно"
        print(f"Air: AQI={aqi}, {status}")
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
        origin = "50.59587618912401,30.56582047829475"
        dest   = "50.52299641605543,30.498424434465736"
        # Один запит, два напрямки: origin->dest і dest->origin
        url = (
            "https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origin}|{dest}"
            f"&destinations={dest}|{origin}"
            f"&mode=driving&departure_time=now&language=uk&key={key}"
        )
        data = requests.get(url, timeout=5).json()

        def parse_leg(row_idx, el_idx, label):
            el = data["rows"][row_idx]["elements"][el_idx]
            if el["status"] != "OK":
                return {"time": "—", "delay": "Немає даних", "delay_min": 0}
            dur = el["duration_in_traffic"]["value"] // 60
            dur_n = el["duration"]["value"] // 60
            delay = dur - dur_n
            if delay <= 2:    txt = "Вільно"
            elif delay <= 10: txt = "Помірно"
            elif delay <= 20: txt = "Затори"
            else:             txt = "Стоїмо"
            print(f"Traffic {label}: {dur} хв, {txt}")
            return {"time": f"{dur} хв", "delay": txt, "delay_min": delay}

        to_kyiv   = parse_leg(0, 1, "До Києва")
        from_kyiv = parse_leg(1, 0, "З Києва")
        return {"to": to_kyiv, "from": from_kyiv}

    except Exception as e:
        print("Traffic error:", e)
        return {
            "to":   {"time": "—", "delay": "Помилка", "delay_min": 0},
            "from": {"time": "—", "delay": "Помилка", "delay_min": 0},
        }


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
                if "Київська" in text or "всі області" in text.lower():
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
    f_big    = ImageFont.truetype(FONT_PATH, 62)
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

if both_on:    tp = C_GREEN;  power_summary = "Світло скрізь є"
elif any_on:   tp = C_ORANGE; power_summary = "Частково є"
else:          tp = C_RED;    power_summary = "Світла немає"

draw_card(L, TY, CW, CH, tp)
label(L+PX, TY+PY, "СВІТЛО", tp["dark"])

draw_dot(L+PX+10, TY+82, C_GREEN["accent"] if s1_on else C_RED["accent"])
t_med(L+PX+28, TY+70, f"Хотянівка: {power['hotyanivka']}", tp["dark"])

draw_dot(L+PX+10, TY+130, C_GREEN["accent"] if s2_on else C_RED["accent"])
t_med(L+PX+28, TY+118, f"ПБХ/Осещина: {power['pbkh']}", tp["dark"])

t_small(L+PX, TY+192, power_summary, tp["accent"])

# ============================================
# 2. ТРИВОГА
# ============================================

ta = C_RED if alert["active"] else C_GREEN
draw_card(R, TY, CW, CH, ta)
label(R+PX, TY+PY, "ТРИВОГА", ta["dark"])
t_big(R+PX, TY+58, "ТРИВОГА" if alert["active"] else "НЕМАЄ", ta["dark"])
draw_dot(R+PX+10, TY+205, C_RED["accent"] if alert["active"] else C_GREEN["accent"])
t_small(R+PX+28, TY+193, "Вишгородський р-н", ta["dark"])

# ============================================
# 3. КУРС ВАЛЮТ
# ============================================

draw_card(L, TY+S, CW, CH, C_BLUE)
label(L+PX, TY+S+PY, "КУРС ВАЛЮТ", C_BLUE["dark"])
t_big(L+PX, TY+S+58,  f"USD {currency['usd_buy']} / {currency['usd_sale']}", C_BLUE["dark"])
t_med(L+PX, TY+S+145, f"EUR {currency['eur_buy']} / {currency['eur_sale']}", C_BLUE["accent"])
t_small(L+PX, TY+S+200, "купівля / продаж", C_BLUE["accent"])

# ============================================
# 4. ПАЛИВО
# ============================================

draw_card(R, TY+S, CW, CH, C_YELLOW)
label(R+PX, TY+S+PY, f"ПАЛИВО · {fuel['station']}", C_YELLOW["dark"])
t_big(R+PX, TY+S+58,  f"А-95  {fuel['a95']}", C_YELLOW["dark"])
t_med(R+PX, TY+S+145, f"Газ: {fuel['gas']}   Диз: {fuel['diesel']}", C_YELLOW["dark"])
t_small(R+PX, TY+S+200, "грн/літр", C_YELLOW["accent"])

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
label(L+PX, TY+S*2+PY, "ЯКІСТЬ ПОВІТРЯ · Хотянівка", ta_air["dark"])
t_big(L+PX, TY+S*2+58,  f"AQI {aqi_val}", ta_air["dark"])
t_med(L+PX, TY+S*2+145, air["status"],    ta_air["accent"])

# ============================================
# 6. ПОГОДА / ПОПЕРЕДЖЕННЯ
# ============================================

w = weather
if w["warning"] and w["warning_level"]:
    # Є попередження
    level_colors = {"I": C_YELLOW, "II": C_ORANGE, "III": C_RED}
    tw = level_colors.get(w["warning_level"], C_YELLOW)

    draw_card(R, TY+S*2, CW, CH, tw)
    label(R+PX, TY+S*2+PY, f"ПОПЕРЕДЖЕННЯ · {w['warning_level']} рівень", tw["dark"])

    # Скорочуємо текст попередження до двох рядків
    warn_text = w["warning"]
    # Видаляємо дату з початку якщо є
    import re
    warn_text = re.sub(r"^[А-Яа-яІіЇїЄє\s\d]+\d{1,2}\s\w+\s", "", warn_text)
    warn_text = warn_text[:120]  # обрізаємо

    # Ділимо на два рядки по ~40 символів
    if len(warn_text) > 40:
        split = warn_text[:40].rfind(" ")
        line1 = warn_text[:split]
        line2 = warn_text[split+1:split+80]
    else:
        line1 = warn_text
        line2 = ""

    t_small(R+PX, TY+S*2+70,  line1, tw["dark"])
    t_small(R+PX, TY+S*2+100, line2, tw["dark"])

    if w["wind"] > 0:
        t_med(R+PX, TY+S*2+145, f"Вітер {w['wind']} м/с", tw["dark"])

else:
    # Звичайна погода
    draw_card(R, TY+S*2, CW, CH, C_TEAL)
    label(R+PX, TY+S*2+PY, "ПОГОДА · Хотянівка", C_TEAL["dark"])
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

to_k   = traffic["to"]
from_k = traffic["from"]

# Колір блоку
to_delay   = to_k["delay_min"]
from_delay = from_k["delay_min"]
max_delay  = max(to_delay, from_delay)

if max_delay <= 2:    tr_theme = C_GREEN
elif max_delay <= 10: tr_theme = C_ORANGE
else:                 tr_theme = C_RED

draw_card(L, ROAD_Y, ROAD_W, ROAD_H, tr_theme)
label(L+PX, ROAD_Y+PY, "ДОРОГА · м. Героїв Дніпра", tr_theme["dark"])

# Ліва — З Києва
t_small(L+PX, ROAD_Y+62,  "З Києва:",        tr_theme["dark"])
t_big(L+PX,   ROAD_Y+90,  from_k["time"],    tr_theme["dark"])
t_med(L+PX,   ROAD_Y+175, from_k["delay"],   tr_theme["accent"])

# Права — До Києва
t_small(RX, ROAD_Y+62,  "До Києва:",       tr_theme["dark"])
t_big(RX,   ROAD_Y+90,  to_k["time"],      tr_theme["dark"])
t_med(RX,   ROAD_Y+175, to_k["delay"],     tr_theme["accent"])

# Вертикальний розділювач
MID_X = L + ROAD_W // 2
draw.rectangle([MID_X, ROAD_Y+50, MID_X+2, ROAD_Y+ROAD_H-30], fill=BORDER)

# ============================================
# ФУТЕР
# ============================================

fy = ROAD_Y + ROAD_H + 20
draw.rectangle([38, fy, WIDTH-38, fy+2], fill=BORDER)
t_small(50, fy+14, "Дані оновлюються кожні 10 хв",        SUBTEXT)
draw.text((50, fy+48), "Поруч | Хотянівка  •  @poruch_ua_bot", fill=TEXT, font=f_footer)
draw.text((960, fy+54), "v1.0", fill="#BBBBBB", font=f_tiny)

# ============================================
# SAVE
# ============================================

img.save("status.png")
print("DONE")
