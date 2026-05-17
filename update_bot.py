import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ============================================
# DATA
# ============================================

def get_rates():
    try:
        res = requests.get(
            'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5',
            timeout=5
        ).json()

        usd = next(item for item in res if item['ccy'] == 'USD')
        eur = next(item for item in res if item['ccy'] == 'EUR')

        return {
            "usd": round(float(usd['sale']), 2),
            "eur": round(float(eur['sale']), 2)
        }

    except Exception as e:
        print("Rates error:", e)

        return {
            "usd": "—",
            "eur": "—"
        }


# ============================================
# CARD DRAWER
# ============================================

def draw_card(
    draw,
    x,
    y,
    w,
    h,
    title,
    value,
    subtitle,
    circle_color,
    accent_color,
    font_title,
    font_value,
    font_small
):

    # card
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=28,
        fill="#FFFDF8",
        outline="#D9D9D9",
        width=2
    )

    # icon circle
    draw.ellipse(
        [x + 25, y + 35, x + 125, y + 135],
        fill=circle_color
    )

    # title
    draw.text(
        (x + 150, y + 28),
        title,
        fill="#0A3D33",
        font=font_title
    )

    # value
    draw.text(
        (x + 150, y + 78),
        value,
        fill="#0A3D33",
        font=font_value
    )

    # subtitle
    draw.text(
        (x + 150, y + 160),
        subtitle,
        fill=accent_color,
        font=font_small
    )


# ============================================
# IMAGE
# ============================================

def create_image():

    width = 1080
    height = 1920

    image = Image.new("RGB", (width, height), "#F7F4EC")
    draw = ImageDraw.Draw(image)

    # ========================================
    # FONTS
    # ========================================

    font_path = "Montserrat-Bold.ttf"

    try:

        font_logo = ImageFont.truetype(font_path, 82)
        font_header = ImageFont.truetype(font_path, 38)

        font_card_title = ImageFont.truetype(font_path, 28)
        font_card_value = ImageFont.truetype(font_path, 54)
        font_small = ImageFont.truetype(font_path, 24)

    except:

        font_logo = ImageFont.load_default()
        font_header = ImageFont.load_default()

        font_card_title = ImageFont.load_default()
        font_card_value = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # ========================================
    # TIME
    # ========================================

    kyiv_time = datetime.utcnow() + timedelta(hours=3)

    date_text = kyiv_time.strftime("%d.%m.%Y")
    time_text = kyiv_time.strftime("%H:%M")

    # ========================================
    # HEADER
    # ========================================

    draw.text(
        (300, 70),
        "ПОРУЧ",
        fill="#054538",
        font=font_logo
    )

    draw.text(
        (300, 165),
        "СТАН ГРОМАДИ",
        fill="#054538",
        font=font_header
    )

    draw.text(
        (300, 225),
        "Хотянівка • Вишгород",
        fill="#2E6E56",
        font=font_header
    )

    # update time

    draw.text(
        (820, 80),
        "Оновлено",
        fill="#054538",
        font=font_small
    )

    draw.text(
        (820, 135),
        date_text,
        fill="#054538",
        font=font_small
    )

    draw.text(
        (820, 185),
        time_text,
        fill="#054538",
        font=font_header
    )

    # ========================================
    # DATA
    # ========================================

    rates = get_rates()

    # ========================================
    # CARDS
    # ========================================

    card_w = 470
    card_h = 320

    left_x = 50
    right_x = 560

    row1 = 350
    row2 = 700
    row3 = 1050
    row4 = 1400

    # ========================================
    # 1. LIGHT
    # ========================================

    draw_card(
        draw,
        left_x,
        row1,
        card_w,
        card_h,
        "1. СВІТЛО",
        "Є",
        "● Стабільно",
        "#E6F1D9",
        "#3A963E",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # 2. ALERT
    # ========================================

    draw_card(
        draw,
        right_x,
        row1,
        card_w,
        card_h,
        "2. ТРИВОГА",
        "НЕМАЄ",
        "● Тихо в області",
        "#FFE4E1",
        "#3A963E",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # 3. USD
    # ========================================

    draw_card(
        draw,
        left_x,
        row2,
        card_w,
        card_h,
        "3. КУРС ВАЛЮТ",
        f"USD {rates['usd']}",
        f"EUR {rates['eur']}",
        "#E4EEF4",
        "#2E6E56",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # 4. FUEL
    # ========================================

    draw_card(
        draw,
        right_x,
        row2,
        card_w,
        card_h,
        "4. ПАЛИВО",
        "A95 55.90",
        "Авантаж 7",
        "#FFF1CC",
        "#F39C12",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # 5. AIR
    # ========================================

    draw_card(
        draw,
        left_x,
        row3,
        card_w,
        card_h,
        "5. ПОВІТРЯ",
        "AQI 62",
        "● Добре",
        "#ECE5F4",
        "#3A963E",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # 6. TO KYIV
    # ========================================

    draw_card(
        draw,
        right_x,
        row3,
        card_w,
        card_h,
        "6. ДО КИЄВА",
        "38 хв",
        "м. Героїв Дніпра",
        "#EEE5F7",
        "#E6A500",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # 7. FROM KYIV
    # ========================================

    draw_card(
        draw,
        left_x,
        row4,
        card_w,
        240,
        "7. З КИЄВА",
        "42 хв",
        "до Вишгорода",
        "#EEE5F7",
        "#E6A500",
        font_card_title,
        font_card_value,
        font_small
    )

    # ========================================
    # FOOTER
    # ========================================

    draw.text(
        (60, 1800),
        "ЛОКАЛЬНЕ. КОРИСНЕ. НАШЕ.",
        fill="#054538",
        font=font_header
    )

    draw.text(
        (60, 1850),
        "poruch.bot",
        fill="#054538",
        font=font_small
    )

    draw.text(
        (860, 1840),
        "v0.1",
        fill="#888888",
        font=font_small
    )

    # ========================================
    # SAVE
    # ========================================

    image.save("status.png")

    print("status.png generated")


# ============================================
# RUN
# ============================================

create_image()
