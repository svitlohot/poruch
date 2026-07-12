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
C_PURPLE = {"bg": "#F3E5F5", "accent": "#8E24AA", "dark": "#6A1B9A"}

# ============================================
# ДАНІ
# ============================================

def get_alert():
    try:
        url = "https://siren.pp.ua/api/v3/alerts"
        data = requests.get(url, timeout=5).json()
        zhmery = next((r for r in data if r.get("regionId") == "180"), None)
        active = zhmery and bool(zhmery.get("activeAlerts"))
        print(f"Alert: {'ТРИВОГА' if active else 'Тихо'}")
        return {"active": bool(active)}
    except Exception as e:
        print("Alert error:", e)
        return {"active": False}


def get_fuel():
    try:
        from bs4 import BeautifulSoup
        url = "https://index.minfin.com.ua/ua/markets/fuel/tm/okko/"
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        # Шукаємо рядок Вінницька в таблиці ОККО
        row = soup.find("a", string="Вінницька")
        if row:
            cells = row.find_parent("tr").find_all("td")
            print("Fuel cells:", [c.text.strip() for c in cells])
            a95p   = cells[1].text.strip() if len(cells) > 1 else "—"  # А-95+
            a95    = cells[2].text.strip() if len(cells) > 2 else "—"  # А-95
            diesel = cells[4].text.strip() if len(cells) > 4 else "—"  # ДП
            gas    = cells[5].text.strip() if len(cells) > 5 else "—"  # Газ
        else:
            a95p = a95 = diesel = gas = "—"

        print(f"Fuel ОККО: A95={a95}, Diesel={diesel}, Gas={gas}")
        return {"a95": a95, "a95p": a95p, "diesel": diesel, "gas": gas}
    except Exception as e:
        print("Fuel error:", e)
        return {"a95": "—", "a95p": "—", "diesel": "—", "gas": "—"}


def get_air():
    try:
        url = "https://www.saveecobot.com/en/maps/vinnytsia.json"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        print("Air raw response:", resp.text[:200])
        data = resp.json()
        aqi = int(data["aqi"])

        if aqi <= 50:    status = "Добра якість"
        elif aqi <= 100: status = "Помірна якість"
        elif aqi <= 150: status = "Шкідливо для чутливих"
        elif aqi <= 200: status = "Шкідливий рівень"
        elif aqi <= 300: status = "Дуже шкідливо"
        else:            status = "Небезпечно"

        print(f"Air (Вінниця): AQI={aqi}, {status}")
        return {"aqi": aqi, "status": status}
    except Exception as e:
        print("Air error:", e)
        return {"aqi": "—", "status": "Помилка"}


def get_weather():
    """Погода + попередження від УкрГМЦ для Вінницької обл."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=49.0356&longitude=28.1138"
            "&current=temperature_2m,weathercode,windspeed_10m"
            "&windspeed_unit=ms"
        )
        data = requests.get(url, timeout=5).json()
        temp = round(data["current"]["temperature_2m"])
        code = data["current"]["weathercode"]
        wind = round(data["current"]["windspeed_10m"])

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

        warning = None
        warning_level = None
        try:
            from bs4 import BeautifulSoup
            w_url = "https://www.meteo.gov.ua/ua/Meteorolohichni-poperedzhennya"
            html = requests.get(w_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")

            headers_h5 = soup.find_all("h5")
            for h in headers_h5:
                text = h.text.strip()
                keywords = ["Вінницьк", "всі област", "по всій", "центральних", "Україні"]
                if any(k in text for k in keywords):
                    warning = text
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


def get_geomagnetic():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        data = requests.get(url, timeout=5).json()
        print("Geomagnetic raw last rows:", data[-3:])

        # Останній запис — поточний Kp
        # Формат: список словників {"time_tag":..., "Kp":..., ...}
        last = data[-1]
        kp = float(last["Kp"])

        if kp < 4:
            status = "Невеликі збурення"
            theme = C_GREEN
        elif kp < 5:
            status = "Невеликі збурення"
            theme = C_GREEN
        elif kp < 6:
            status = "Слабка буря"
            theme = C_YELLOW
        elif kp < 7:
            status = "Помірна буря"
            theme = C_ORANGE
        elif kp < 8:
            status = "Сильна буря"
            theme = C_ORANGE
        elif kp < 9:
            status = "Шторм"
            theme = C_RED
        else:
            status = "Екстремальний шторм"
            theme = C_RED

        print(f"Geomagnetic: Kp={kp}, {status}")
        return {"kp": f"{kp:.1f}", "status": status, "theme": theme}
    except Exception as e:
        print("Geomagnetic error:", e)
        return {"kp": "—", "status": "Помилка", "theme": C_TEAL}


def get_geomagnetic_forecast():
    """Максимальний прогнозований Kp на завтра (NOAA 3-day forecast)"""
    try:
        url = "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
        text = requests.get(url, timeout=10).text
        import re
        match = re.search(r"NOAA Kp index breakdown.*?\n(.*?)\n\n", text, re.DOTALL)
        block = match.group(1) if match else ""
        lines = block.strip().split("\n")

        max_tomorrow = 0.0
        for line in lines[1:]:
            parts = line.split()
            nums = []
            for token in parts[1:]:
                try:
                    nums.append(float(token))
                except ValueError:
                    pass
            if len(nums) >= 2 and nums[1] > max_tomorrow:
                max_tomorrow = nums[1]

        print(f"Forecast tomorrow max Kp: {max_tomorrow}")
        return max_tomorrow
    except Exception as e:
        print("Forecast error:", e)
        return None


def kp_status(kp):
    if kp < 5: return "Невеликі збурення", C_GREEN
    if kp < 6: return "Слабка буря", C_YELLOW
    if kp < 7: return "Помірна буря", C_ORANGE
    if kp < 8: return "Сильна буря", C_ORANGE
    if kp < 9: return "Шторм", C_RED
    return "Екстремальний шторм", C_RED


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
    has_emoji = True
except:
    has_emoji = False

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
draw.text((tx, 30),  "СТАН МІСТА",  fill=TEXT,    font=f_header)
draw.text((tx, 118), "Жмеринка",    fill=SUBTEXT, font=f_sub)

draw.text((820, 30),  "Оновлено",               fill=SUBTEXT, font=f_tiny)
draw.text((820, 58),  now.strftime("%d.%m.%Y"), fill=TEXT,    font=f_small)
draw.text((820, 95),  now.strftime("%H:%M"),    fill=TEXT,    font=f_time)

draw.rectangle([0, HEADER_H, WIDTH, HEADER_H+3], fill=BORDER)

# ============================================
# ДОПОМІЖНІ ФУНКЦІЇ
# ============================================

L   = 38
R   = 558
TY  = HEADER_H + 22
S   = 286
CW  = 482
CH  = 258
PX  = 26
PY  = 18

def draw_card(x, y, w, h, theme):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=28, fill=theme["bg"], outline=BORDER, width=2)

def draw_dot(x, y, color):
    draw.ellipse([x-10, y-10, x+10, y+10], fill=color)

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

alert  = get_alert()
fuel   = get_fuel()
air    = get_air()
weather = get_weather()
geo    = get_geomagnetic()
geo_forecast = get_geomagnetic_forecast()

# ============================================
# 1. ТРИВОГА
# ============================================

ta = C_RED if alert["active"] else C_GREEN
draw_card(L, TY, CW, CH, ta)
label_with_emoji(L+PX, TY+PY, "🚨", "ТРИВОГА", ta["dark"])
t_big(L+PX, TY+58, "ТРИВОГА" if alert["active"] else "НЕМАЄ", ta["dark"])
draw_dot(L+PX+10, TY+205, C_RED["accent"] if alert["active"] else C_GREEN["accent"])
t_small(L+PX+28, TY+193, "Жмеринська громада", ta["dark"])

# ============================================
# 2. ПАЛИВО ОККО
# ============================================

draw_card(R, TY, CW, CH, C_YELLOW)
label_with_emoji(R+PX, TY+PY, "⛽", "ПАЛИВО · ОККО", C_YELLOW["dark"])
t_big(R+PX, TY+55,   f"А-95  {fuel['a95']}", C_YELLOW["dark"])
t_med(R+PX, TY+130,  f"Газ: {fuel['gas']}   Диз: {fuel['diesel']}", C_YELLOW["dark"])
t_small(R+PX, TY+195, "грн/літр · Вінницька обл.", C_YELLOW["accent"])

# ============================================
# 3. ЯКІСТЬ ПОВІТРЯ
# ============================================

aqi_val = air["aqi"]
if isinstance(aqi_val, int):
    if aqi_val <= 40:   ta_air = C_GREEN
    elif aqi_val <= 80: ta_air = C_ORANGE
    else:               ta_air = C_RED
else:
    ta_air = C_TEAL

draw_card(L, TY+S, CW, CH, ta_air)
label_with_emoji(L+PX, TY+S+PY, "🌿", "ЯКІСТЬ ПОВІТРЯ · Вінниця", ta_air["dark"])
t_big(L+PX, TY+S+58,  f"AQI {aqi_val}", ta_air["dark"])
t_med(L+PX, TY+S+145, air["status"],    ta_air["accent"])
t_small(L+PX, TY+S+200, "Дані: SaveEcoBot", ta_air["accent"])

# ============================================
# 4. ПОГОДА / ПОПЕРЕДЖЕННЯ
# ============================================

w = weather
if w["warning"] and w["warning_level"]:
    import re

    warn_text = w["warning"]

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

    for keyword in ["областях ", "районах "]:
        idx = warn_text.rfind(keyword)
        if idx != -1:
            warn_text = warn_text[idx + len(keyword):]
            break

    warn_text = re.sub(r'\([^)]*рівень[^)]*\)', '', warn_text).strip().rstrip(".")

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

    draw_card(R, TY+S, CW, CH, tw)
    label_with_emoji(R+PX, TY+S+PY, "⛈", f"ПОПЕРЕДЖЕННЯ · {w['warning_level']} рівень {date_str}", tw["dark"])

    for i, line in enumerate(lines[:3]):
        t_small(R+PX, TY+S+58 + i*34, line, tw["dark"])

    if w["wind"] > 0:
        t_med(R+PX, TY+S+175, f"Вітер {w['wind']} м/с", tw["dark"])

else:
    draw_card(R, TY+S, CW, CH, C_TEAL)
    label_with_emoji(R+PX, TY+S+PY, "🌤", "ПОГОДА · Жмеринка", C_TEAL["dark"])
    t_big(R+PX, TY+S+58,  f"+{w['temp']}°", C_TEAL["dark"])
    t_med(R+PX, TY+S+145, w["desc"],         C_TEAL["accent"])
    if w["wind"] > 0:
        t_small(R+PX, TY+S+200, f"Вітер {w['wind']} м/с", C_TEAL["accent"])

# ============================================
# 5. ГЕОМАГНІТНА ОБСТАНОВКА (повна ширина)
# ============================================

GEO_Y = TY + S*2
GEO_H = 320
GEO_W = WIDTH - L*2
gt = geo["theme"]

draw_card(L, GEO_Y, GEO_W, GEO_H, gt)
label_with_emoji(L+PX, GEO_Y+PY, "🧲", "ГЕОМАГНІТНА ОБСТАНОВКА · Kp-індекс", gt["dark"])
t_big(L+PX, GEO_Y+62,  f"Kp {geo['kp']}", gt["dark"])
t_med(L+PX, GEO_Y+148, geo["status"],      gt["accent"])

if geo_forecast is not None and geo_forecast >= 5:
    f_status, f_theme = kp_status(geo_forecast)
    draw_dot(L+PX+10, GEO_Y+200, f_theme["accent"])
    t_small(L+PX+28, GEO_Y+188, f"Завтра можлива буря: до Kp {geo_forecast:.0f} ({f_status})", gt["dark"])
    t_small(L+PX, GEO_Y+250, "Дані: NOAA Space Weather Prediction Center", gt["accent"])
else:
    t_small(L+PX, GEO_Y+250, "Дані: NOAA Space Weather Prediction Center", gt["accent"])

# ============================================
# ФУТЕР
# ============================================

fy = GEO_Y + GEO_H + 20
draw.rectangle([38, fy, WIDTH-38, fy+2], fill=BORDER)
t_small(50, fy+14, "Дані оновлюються кожні 10 хв", SUBTEXT)
draw.text((50, fy+48), "Поруч | Жмеринка  •  @poruch_ua_bot", fill=TEXT, font=f_footer)
draw.text((960, fy+54), "v1.0", fill="#BBBBBB", font=f_tiny)

# ============================================
# SAVE
# ============================================

img.save("zhmerynka.png", optimize=True, compress_level=9)
print("DONE")
