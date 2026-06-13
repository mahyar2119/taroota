import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "YOUR_TOKEN"
ADMIN_ID = 107713088

logging.basicConfig(level=logging.INFO)

# ── تایم‌اسلات‌ها ──
BREAK_START = "12:30"
BREAK_END = "14:00"

def get_time_slots():
    slots = []
    start = datetime.strptime("10:00", "%H:%M")
    end = datetime.strptime("16:00", "%H:%M")
    break_s = datetime.strptime(BREAK_START, "%H:%M")
    break_e = datetime.strptime(BREAK_END, "%H:%M")
    current = start
    while current < end:
        if not (break_s <= current < break_e):
            slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    return slots

def get_next_7_days():
    days = []
    today = datetime.now()
    fa_days = {0:"دوشنبه",1:"سه‌شنبه",2:"چهارشنبه",3:"پنج‌شنبه",4:"جمعه",5:"شنبه",6:"یک‌شنبه"}
    for i in range(1, 8):
        day = today + timedelta(days=i)
        fa_name = fa_days[day.weekday()]
        date_str = day.strftime("%Y/%m/%d")
        days.append((fa_name, date_str))
    return days

# ── بوکینگ‌های ثبت‌شده (در حافظه) ──
bookings = {}

def is_slot_taken(date, time):
    return bookings.get(f"{date}_{time}", False)

def book_slot(date, time, user_id):
    bookings[f"{date}_{time}"] = user_id

# ── استارت ──
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🔮 رزرو فال تصویری آنلاین", callback_data="book")],
        [InlineKeyboardButton("💫 اشتراک فال سه‌کارتی", callback_data="subscribe")],
        [InlineKeyboardButton("🌐 ورود به سایت تاروتا", url="https://taroota-app.vercel.app")],
    ]
    await update.message.reply_text(
        f"🔮 سلام {user.first_name} عزیز!\n\n"
        "به تاروتا خوش اومدی 🌟\n\n"
        "✨ خدمات ما:\n"
        "• کارت روز رایگان در سایت\n"
        "• فال سه‌کارتی AI (اشتراکی)\n"
        "• فال تصویری آنلاین — $30 / 30 دقیقه\n\n"
        "چی می‌خوای؟ 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── رزرو — انتخاب روز ──
async def book_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    days = get_next_7_days()
    keyboard = []
    for fa_name, date_str in days:
        keyboard.append([InlineKeyboardButton(
            f"📅 {fa_name} — {date_str}",
            callback_data=f"day_{date_str}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_main")])
    await query.message.reply_text(
        "📅 روز مورد نظرت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── انتخاب ساعت ──
async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date_str = query.data.replace("day_", "")
    context.user_data['selected_date'] = date_str
    slots = get_time_slots()
    keyboard = []
    row = []
    for i, slot in enumerate(slots):
        if is_slot_taken(date_str, slot):
            row.append(InlineKeyboardButton(f"❌ {slot}", callback_data="taken"))
        else:
            row.append(InlineKeyboardButton(f"✅ {slot}", callback_data=f"time_{slot}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="book")])
    await query.message.reply_text(
        f"🕐 ساعت مورد نظرت رو انتخاب کن:\n📅 تاریخ: {date_str}\n\n✅ آزاد  |  ❌ رزرو شده",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ── اسلات گرفته شده ──
async def slot_taken(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("این ساعت رزرو شده! ساعت دیگه‌ای انتخاب کن 🙏", show_alert=True)

# ── تأیید ساعت — درخواست اطلاعات ──
async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_str = query.data.replace("time_", "")
    date_str = context.user_data.get('selected_date', '')
    context.user_data['selected_time'] = time_str
    context.user_data['waiting_for'] = 'booking_info'
    await query.message.reply_text(
        f"✅ وقت انتخابی:\n"
        f"📅 تاریخ: {date_str}\n"
        f"🕐 ساعت: {time_str}\n\n"
        f"💰 هزینه: $30 / 30 دقیقه\n\n"
        f"لطفاً اطلاعات زیر رو بفرست:\n\n"
        f"1️⃣ نام و نام خانوادگی\n"
        f"2️⃣ شماره واتساپ/تلگرام\n"
        f"3️⃣ کشور محل سکونت\n"
        f"4️⃣ موضوع فال (اختیاری)"
    )

# ── اشتراک ──
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("ماهانه — $9", callback_data="plan_monthly")],
        [InlineKeyboardButton("۳ ماهه — $21 (۲۲٪ تخفیف)", callback_data="plan_3month")],
        [InlineKeyboardButton("۶ ماهه — $36 (۳۳٪ تخفیف)", callback_data="plan_6month")],
        [InlineKeyboardButton("سالانه — $60 (۴۴٪ تخفیف)", callback_data="plan_yearly")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_main")],
    ]
    await query.message.reply_text(
        "💫 پلن اشتراک خودت رو انتخاب کن:\n\n"
        "✅ فال سه‌کارتی AI نامحدود\n"
        "✅ فال عشق، شغل، سلامت\n"
        "✅ تاریخچه فال‌ها",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plans = {
        "plan_monthly": ("ماهانه", "$9"),
        "plan_3month": ("۳ ماهه", "$21"),
        "plan_6month": ("۶ ماهه", "$36"),
        "plan_yearly": ("سالانه", "$60"),
    }
    plan_name, plan_price = plans.get(query.data, ("نامشخص", ""))
    context.user_data['waiting_for'] = 'subscribe_info'
    context.user_data['plan'] = f"{plan_name} — {plan_price}"
    await query.message.reply_text(
        f"✅ پلن انتخابی: {plan_name} — {plan_price}\n\n"
        "لطفاً اطلاعات زیر رو بفرست:\n\n"
        "1️⃣ نام و نام خانوادگی\n"
        "2️⃣ شماره واتساپ/تلگرام\n"
        "3️⃣ کشور محل سکونت"
    )

# ── برگشت به منوی اصلی ──
async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔮 رزرو فال تصویری آنلاین", callback_data="book")],
        [InlineKeyboardButton("💫 اشتراک فال سه‌کارتی", callback_data="subscribe")],
        [InlineKeyboardButton("🌐 ورود به سایت تاروتا", url="https://taroota-app.vercel.app")],
    ]
    await query.message.reply_text("منوی اصلی 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# ── دریافت پیام ──
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    waiting = context.user_data.get('waiting_for', '')

    if waiting == 'booking_info':
        date_str = context.user_data.get('selected_date', '')
        time_str = context.user_data.get('selected_time', '')
        book_slot(date_str, time_str, user.id)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 رزرو جدید!\n\n"
                 f"👤 {user.first_name} {user.last_name or ''}\n"
                 f"🆔 @{user.username or 'ندارد'}\n"
                 f"🔑 ID: {user.id}\n"
                 f"📅 تاریخ: {date_str}\n"
                 f"🕐 ساعت: {time_str}\n\n"
                 f"📝 اطلاعات:\n{text}"
        )
        await update.message.reply_text(
            f"✅ رزرو شما با موفقیت ثبت شد!\n\n"
            f"📅 تاریخ: {date_str}\n"
            f"🕐 ساعت: {time_str}\n\n"
            f"🔮 تیم تاروتا با شما تماس می‌گیرد و اطلاعات پرداخت ارسال می‌شود.\n\n"
            f"با تاروتا همراه باشید 🌟"
        )
        context.user_data['waiting_for'] = ''

    elif waiting == 'subscribe_info':
        plan = context.user_data.get('plan', '')
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 اشتراک جدید!\n\n"
                 f"👤 {user.first_name} {user.last_name or ''}\n"
                 f"🆔 @{user.username or 'ندارد'}\n"
                 f"🔑 ID: {user.id}\n"
                 f"📦 پلن: {plan}\n\n"
                 f"📝 اطلاعات:\n{text}"
        )
        await update.message.reply_text(
            f"✅ درخواست اشتراک با موفقیت ثبت شد!\n\n"
            f"📦 پلن: {plan}\n\n"
            f"🔮 تیم تاروتا با شما تماس می‌گیرد و اطلاعات پرداخت ارسال می‌شود.\n\n"
            f"با تاروتا همراه باشید 🌟"
        )
        context.user_data['waiting_for'] = ''

    else:
        keyboard = [
            [InlineKeyboardButton("🔮 رزرو فال تصویری", callback_data="book")],
            [InlineKeyboardButton("💫 اشتراک", callback_data="subscribe")],
            [InlineKeyboardButton("🌐 سایت تاروتا", url="https://taroota-app.vercel.app")],
        ]
        await update.message.reply_text(
            "از منوی زیر انتخاب کن 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def reply_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("فرمت: /msg USER_ID پیام")
        return
    user_id = int(context.args[0])
    msg = ' '.join(context.args[1:])
    await context.bot.send_message(chat_id=user_id, text=f"🔮 تاروتا:\n\n{msg}")
    await update.message.reply_text("✅ پیام ارسال شد!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("msg", reply_user))
    app.add_handler(CallbackQueryHandler(book_session, pattern="^book$"))
    app.add_handler(CallbackQueryHandler(subscribe, pattern="^subscribe$"))
    app.add_handler(CallbackQueryHandler(plan_selected, pattern="^plan_"))
    app.add_handler(CallbackQueryHandler(select_day, pattern="^day_"))
    app.add_handler(CallbackQueryHandler(select_time, pattern="^time_"))
    app.add_handler(CallbackQueryHandler(slot_taken, pattern="^taken$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🔮 Taroota Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
