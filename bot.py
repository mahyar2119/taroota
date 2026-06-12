import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8909562198:AAE4Pq0wCd5ZjwlwZBdCqv_HgTZ7-JUhhhE"
ADMIN_ID = 107713088

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🔮 رزرو فال تصویری آنلاین", callback_data="book")],
        [InlineKeyboardButton("💫 اشتراک فال سه‌کارتی", callback_data="subscribe")],
        [InlineKeyboardButton("🌐 ورود به سایت تاروتا", url="https://taroota-app.vercel.app")],
    ]
    await update.message.reply_text(
        f"🔮 سلام {user.first_name} عزیز!\n\nبه تاروتا خوش اومدی 🌟\n\nچی می‌خوای؟ 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def book_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📅 لطفاً اطلاعات زیر رو بفرست:\n\n1️⃣ نام و نام خانوادگی\n2️⃣ شماره واتساپ/تلگرام\n3️⃣ کشور محل سکونت\n4️⃣ روز و ساعت مناسب\n5️⃣ موضوع فال (اختیاری)\n\n💰 هزینه: $30 / 30 دقیقه"
    )
    context.user_data['waiting_for'] = 'booking'

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("ماهانه — $9", callback_data="plan_monthly")],
        [InlineKeyboardButton("۳ ماهه — $21", callback_data="plan_3month")],
        [InlineKeyboardButton("۶ ماهه — $36", callback_data="plan_6month")],
        [InlineKeyboardButton("سالانه — $60", callback_data="plan_yearly")],
    ]
    await query.message.reply_text("💫 پلن خودت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))

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
    context.user_data['waiting_for'] = 'subscribe'
    context.user_data['plan'] = f"{plan_name} — {plan_price}"
    await query.message.reply_text(
        f"✅ پلن: {plan_name} — {plan_price}\n\nلطفاً بفرست:\n\n1️⃣ نام و نام خانوادگی\n2️⃣ شماره واتساپ/تلگرام\n3️⃣ کشور محل سکونت"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    waiting = context.user_data.get('waiting_for', '')
    if waiting in ['booking', 'subscribe']:
        plan_info = f"\n📦 پلن: {context.user_data.get('plan', '')}" if waiting == 'subscribe' else ""
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 درخواست جدید!\n\n👤 {user.first_name} {user.last_name or ''}\n🆔 @{user.username or 'ندارد'}\n🔑 ID: {user.id}\n📋 {'رزرو فال تصویری' if waiting == 'booking' else 'اشتراک'}{plan_info}\n\n📝 {text}"
        )
        await update.message.reply_text("✅ دریافت شد!\n\n🔮 تیم تاروتا به زودی باهات تماس می‌گیره 🌟")
        context.user_data['waiting_for'] = ''
    else:
        keyboard = [
            [InlineKeyboardButton("🔮 رزرو فال تصویری", callback_data="book")],
            [InlineKeyboardButton("💫 اشتراک", callback_data="subscribe")],
            [InlineKeyboardButton("🌐 سایت تاروتا", url="https://taroota-app.vercel.app")],
        ]
        await update.message.reply_text("از منوی زیر انتخاب کن 👇", reply_markup=InlineKeyboardMarkup(keyboard))

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🔮 Taroota Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()