from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
import io
import nest_asyncio
import asyncio
import random
import os

# =====================================================
# PNL CARD IMAGE GENERATOR
# =====================================================

def create_pnl_card(
    coin,
    entry_price,
    mark_price,
    lev,
    margin=round(random.uniform(70, 145), 1),
    starttype="long"
):
    # ---------------- Calculations ----------------
# ---------------- REAL FUTURES MATH ----------------
    position = margin * lev

    if starttype == "long":
        unrealized_pnl = position * (mark_price - entry_price) / entry_price
    else:
        unrealized_pnl = position * (entry_price - mark_price) / entry_price

    roi = (unrealized_pnl / margin) * 100

    # maintenance margin (0.5% typical Binance)
    maintenance = position * 0.005
    equity = margin + unrealized_pnl

    if equity <= 0:
        margin_ratio = 100
    else:
        margin_ratio = (maintenance / equity) * 100

    size_usdt = position


    banner = Image.new("RGB", (1080, 620), color=(255,255,255))
    draw = ImageDraw.Draw(banner)

    # ---------------- Share icon ----------------
    center_x, center_y = 1007, 70
    dot_radius = 5
    line_width = 4
    color = (120, 126, 139)

    p1 = (center_x, center_y)
    p2 = (center_x + 19, center_y - 9)
    p3 = (center_x + 19, center_y + 9)

    draw.line([p1, p2], fill=color, width=line_width)
    draw.line([p1, p3], fill=color, width=line_width)

    for x, y in [p1, p2, p3]:
        draw.ellipse((x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius), fill=color)

    # ---------------- Fonts ----------------
    font_path = "fonts/Binance PLEX.ttf"
    font_B = ImageFont.truetype(font_path, 30)
    font_h = ImageFont.truetype(font_path, 39)
    font_pc = ImageFont.truetype(font_path, 20)
    font_alert = ImageFont.truetype("fonts/Arial.ttf", 30)
    font_row = ImageFont.truetype(font_path, 30)
    font_button = ImageFont.truetype("fonts/Arial Bold.ttf", 27)
    font_gnum = ImageFont.truetype(font_path, 49)
    font_num = ImageFont.truetype(font_path, 31)

    COLOR_WHITE = (39,39,39)
    COLOR_GREEN = (42, 202, 138)
    COLOR_RED = (198, 21, 31)
    COLOR_BTN_BG = (245,245,245)
    COLOR_TEXT_DIM = (150, 157, 173)

    # ---------------- Header ----------------
    if starttype == "long":
        draw.rounded_rectangle([38, 48, 79, 89], radius=4, fill=(93, 217, 155))
        draw.text((48, 50), "B", font=font_B, fill=(255,255,255))
    else:
        draw.rounded_rectangle([38, 48, 79, 89], radius=4, fill=(246, 76, 103))
        draw.text((48, 50), "S", font=font_B, fill=(255,255,255))

    coin_text = f"{coin}USDT"
    coin_x, coin_y = 87, 43
    draw.text((coin_x, coin_y), coin_text, font=font_h, fill=(39,39,39))
    bbox = draw.textbbox((coin_x, coin_y), coin_text, font=font_h)
    coin_text_width = bbox[2] - bbox[0]

    bbox = draw.textbbox((coin_x, coin_y), coin_text, font=font_h)
    offset_x = coin_x + (bbox[2] - bbox[0]) + 20

    draw.rounded_rectangle([offset_x, 49, offset_x + 62, 82], radius=7, fill=COLOR_BTN_BG)
    draw.text((offset_x + 9, 54), "Perp", font=font_pc, fill=COLOR_WHITE)

    draw.rounded_rectangle([offset_x + 66, 49, offset_x + 182, 82], radius=7, fill=COLOR_BTN_BG)
    draw.text((offset_x + 81, 55), f"Cross {int(lev)}x", font=font_pc, fill=COLOR_WHITE)

    draw.text((offset_x + 185, 50), "!!!!", font=font_alert, fill=COLOR_RED)

    # ---------------- Data Rows ----------------
    draw.text((38, 130), "Unrealized PNL (USDT)", font=font_row, fill=COLOR_TEXT_DIM)
    bbox = draw.textbbox((38, 130), "Unrealized PNL (USDT)", font=font_row)
    underline_y = bbox[3] + 6  # distance below text

    dot_color = (150, 157, 173, 120)
    dot_radius = 2
    dot_spacing = 8

    x_start, x_end = bbox[0], bbox[2]
    for dx in range(x_start, x_end, dot_spacing):
        draw.ellipse((dx, underline_y, dx + dot_radius, underline_y + dot_radius), fill=dot_color)
    pnl_color = COLOR_GREEN if unrealized_pnl >= 0 else COLOR_RED
    draw.text((38, 172), f"{unrealized_pnl:+.1f}", font=font_gnum, fill=pnl_color)


    draw.text((38, 257), "Size (USDT)", font=font_row, fill=COLOR_TEXT_DIM)
    bbox = draw.textbbox((38, 257), "Size (USDT)", font=font_row)
    underline_y = bbox[3] + 6  # distance below text

    dot_color = (150, 157, 173, 120)
    dot_radius = 2
    dot_spacing = 8

    x_start, x_end = bbox[0], bbox[2]
    for dx in range(x_start, x_end, dot_spacing):
        draw.ellipse((dx, underline_y, dx + dot_radius, underline_y + dot_radius), fill=dot_color)
    draw.text((41, 305), f"{size_usdt:.1f}", font=font_num, fill=COLOR_WHITE)

    draw.text((38, 381), "Entry Price (USDT)", font=font_row, fill=COLOR_TEXT_DIM)
    bbox = draw.textbbox((38, 381), "Entry Price (USDT)", font=font_row)
    underline_y = bbox[3] + 6  # distance below text

    dot_color = (150, 157, 173, 120)
    dot_radius = 2
    dot_spacing = 8

    x_start, x_end = bbox[0], bbox[2]
    for dx in range(x_start, x_end, dot_spacing):
        draw.ellipse((dx, underline_y, dx + dot_radius, underline_y + dot_radius), fill=dot_color)
    draw.text((41, 429), f"{entry_price:.4f}", font=font_num, fill=COLOR_WHITE)

    draw.text((381, 257), "Margin (USDT)", font=font_row, fill=COLOR_TEXT_DIM)
    draw.text((384, 305), f"{margin:.1f}", font=font_num, fill=COLOR_WHITE)

    draw.text((381, 381), "Mark Price (USDT)", font=font_row, fill=COLOR_TEXT_DIM)
    draw.text((384, 429), f"{mark_price:.4f}", font=font_num, fill=COLOR_WHITE)

    # ROI label
    draw.text((993, 130), "ROI", font=font_row, fill=COLOR_TEXT_DIM)
    bbox = draw.textbbox((993, 130), "ROI", font=font_row)
    underline_y = bbox[3] + 6  # distance below text

    dot_color = (150, 157, 173, 120)
    dot_radius = 2
    dot_spacing = 8

    x_start, x_end = bbox[0], bbox[2]
    for dx in range(x_start, x_end, dot_spacing):
        draw.ellipse((dx, underline_y, dx + dot_radius, underline_y + dot_radius), fill=dot_color)


    # Measure ROI label end
    roi_label_bbox = draw.textbbox((993, 130), "ROI", font=font_row)
    roi_label_end_x = roi_label_bbox[2]

    # ROI value
    roi_color = COLOR_GREEN if roi >= 0 else COLOR_RED
    roi_text = f"{roi:+.1f}%"
    roi_value_bbox = draw.textbbox((0, 0), roi_text, font=font_gnum)
    roi_value_width = roi_value_bbox[2] - roi_value_bbox[0]

    # Draw value aligned to end of "I"
    draw.text(
        (roi_label_end_x - roi_value_width, 178),
        roi_text,
        font=font_gnum,
        fill=roi_color
    )

    draw.text((875, 257), "Margin Ratio", font=font_row, fill=COLOR_TEXT_DIM)
    bbox = draw.textbbox((875, 257), "Margin Ratio", font=font_row)
    underline_y = bbox[3] + 6  # distance below text

    dot_color = (150, 157, 173, 120)
    dot_radius = 2
    dot_spacing = 8

    x_start, x_end = bbox[0], bbox[2]
    for dx in range(x_start, x_end, dot_spacing):
        draw.ellipse((dx, underline_y, dx + dot_radius, underline_y + dot_radius), fill=dot_color)
    
    mr_text = f"{margin_ratio:.2f}%"
    mr_bbox = draw.textbbox((0, 0), mr_text, font=font_num)
    mr_color = COLOR_GREEN if margin_ratio < 80 else COLOR_RED
    draw.text((1040 - (mr_bbox[2] - mr_bbox[0]), 305), mr_text, font=font_num, fill=mr_color)


    draw.text((821, 381), "Liq. Price (USDT)", font=font_row, fill=COLOR_TEXT_DIM)
    bbox = draw.textbbox((821, 381), "Liq. Price (USDT)", font=font_row)
    underline_y = bbox[3] + 6  # distance below text

    dot_color = (150, 157, 173, 120)
    dot_radius = 2
    dot_spacing = 8

    x_start, x_end = bbox[0], bbox[2]
    for dx in range(x_start, x_end, dot_spacing):
        draw.ellipse((dx, underline_y, dx + dot_radius, underline_y + dot_radius), fill=dot_color)


    if starttype == "long":
        liq_price = entry_price * (1 - 1/lev)
    else:
        liq_price = entry_price * (1 + 1/lev)

    liq_text = f"{liq_price:.4f}"
    liq_bbox = draw.textbbox((0, 0), liq_text, font=font_num)
    draw.text((1040 - (liq_bbox[2] - liq_bbox[0]), 429), liq_text, font=font_num, fill=COLOR_WHITE)

    # ---------------- Buttons ----------------
    btn_labels = ["Leverage", "TP/SL", "Close"]
    btn_y, btn_h = 504, 80
    btn_gap = 21
    x_start = 37
    total_w = 1080 - (x_start * 2)
    btn_w = (total_w - (2 * btn_gap)) / 3

    for i, label in enumerate(btn_labels):
        bx = x_start + i * (btn_w + btn_gap)
        draw.rounded_rectangle([bx, btn_y, bx + btn_w, btn_y + btn_h], radius=10, fill=COLOR_BTN_BG)
        tb = draw.textbbox((0, 0), label, font=font_button)
        draw.text(
            (bx + (btn_w - (tb[2] - tb[0])) / 2, btn_y + (btn_h - (tb[3] - tb[1])) / 2 - 2),
            label,
            font=font_button,
            fill=COLOR_WHITE
        )

    return banner
# =====================================================
# TELEGRAM BOT
# =====================================================

nest_asyncio.apply()

AUTHORIZED_USERS = [
    5016926422, 1596819214, 7940432188, 5557916671,
    6377200085, 5326140102, 8246496686, 5202229117
]

async def send_pnl_card(update: Update, context: ContextTypes.DEFAULT_TYPE, starttype: str):
    try:
        coin = context.args[0].upper()
        entry_price = float(context.args[1])
        mark_price = float(context.args[2])
        lev = float(context.args[3])
        margin = float(context.args[4]) if len(context.args) > 4 else round(random.uniform(70, 145), 1)
    except Exception:
        await update.message.reply_text(
            f"Usage: /{starttype}pnl <coin> <entry> <mark> <leverage> <margin>"
        )
        return

    img = create_pnl_card(coin, entry_price, mark_price, lev, margin, starttype)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    await update.message.reply_photo(photo=bio)

async def long_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ You need an active subscription.")
        return
    await send_pnl_card(update, context, "long")

async def short_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ You need an active subscription.")
        return
    await send_pnl_card(update, context, "short")


# =====================================================
# BOT STARTUP
# =====================================================

TOKEN = os.getenv("BOT_TOKEN")

request = HTTPXRequest(
    connect_timeout=20,
    read_timeout=20,
    write_timeout=20,
    pool_timeout=20,
)

app = ApplicationBuilder().token(TOKEN).request(request).build()
app.add_handler(CommandHandler("longpnl", long_pnl))
app.add_handler(CommandHandler("shortpnl", short_pnl))

print("🚀 Bot is running...")
app.run_polling()
