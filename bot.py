import telebot
from telebot import types
import logging
import os
import time
from config import BOT_TOKEN, CHANNEL_ID
from rss_fetcher import fetch_recent_news, deduplicate
from ai_classifier import classify_batch

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8",
)
logging.getLogger("telebot").setLevel(logging.CRITICAL)

bot = telebot.TeleBot(BOT_TOKEN)


def format_time(published):
    from datetime import datetime, timezone, timedelta
    try:
        tehran = timezone(timedelta(hours=3, minutes=30))
        dt = published.astimezone(tehran)
        return dt.strftime("%H:%M - %Y/%m/%d")
    except Exception:
        return "اخیر"


def build_message(cat, summary_fa, item):
    if "AI جدید" in cat or "ابزار" in cat:
        hashtag = "#aiجدید"
    elif "Research" in cat or "ریسرچ" in cat:
        hashtag = "#research"
    elif "Coding" in cat or "Agent" in cat:
        hashtag = "#coding"
    elif "شرکت" in cat:
        hashtag = "#aiخبر"
    else:
        hashtag = "#ai"

    time_str = format_time(item.get("published"))

    text = (
        f"🟪\n\n"
        f"{cat}\n"
        f"🕐 {time_str}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *{item['title']}*\n\n"
        f"📝 {summary_fa}\n\n"
        f"🔗 [مطالعه کامل]({item['link']})\n"
        f"🌐 منبع: {item['source']}\n\n"
        f"{hashtag}"
    )
    return text


def do_fetch():
    try:
        print("[FETCH] starting...")
        logging.info("شروع جمع‌آوری")

        news = fetch_recent_news()
        print(f"[FETCH] collected {len(news)}")
        logging.info(f"جمع‌آوری شد: {len(news)} خبر")

        news = deduplicate(news)
        print(f"[FETCH] after dedup: {len(news)}")

        for i, item in enumerate(news):
            item["id"] = i

        results = classify_batch(news, batch_size=5)

        published = 0
        skipped = 0

        for item in news:
            result = results.get(item["id"])
            if not result:
                skipped += 1
                continue

            cat = result.get("category")
            summary_fa = result.get("summary_fa") or ""

            if not cat:
                skipped += 1
                continue

            text = build_message(cat, summary_fa, item)

            try:
                bot.send_message(
                    CHANNEL_ID, text,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
                published += 1
                time.sleep(3)
            except Exception as e:
                print(f"[PUBLISH ERROR] {e}")
                time.sleep(5)

        logging.info(f"منتشر شد: {published} خبر، رد شد: {skipped} خبر")
        print(f"[FETCH] done: {published} published, {skipped} skipped")
        return published, skipped

    except Exception as e:
        import traceback
        logging.error(f"خطا: {e}")
        print(f"[FETCH ERROR] {type(e).__name__}")
        traceback.print_exc()
        return 0, 0


@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("دریافت اخبار", callback_data="fetch_news")
    markup.add(btn)
    bot.reply_to(
        message,
        "سلام! برای دریافت و انتشار اخبار دکمه زیر را بزن:",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data == "fetch_news")
def handle_fetch(call):
    try:
        bot.answer_callback_query(call.id, "در حال جمع‌آوری اخبار...")
        msg = bot.send_message(call.message.chat.id, "در حال جمع‌آوری...")

        published, skipped = do_fetch()

        bot.edit_message_text(
            f"تمام شد!\n{published} خبر منتشر شد.\n{skipped} خبر رد شد.",
            call.message.chat.id, msg.message_id,
        )
    except Exception as e:
        print(f"[HANDLE ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("AUTO_RUN") == "1":
        print("[AUTO MODE] running once...")
        do_fetch()
        print("[AUTO MODE] done.")
    else:
        print("Bot is running...")
        import sys
        import telebot.apihelper
        telebot.apihelper.CONNECT_TIMEOUT = 60
        telebot.apihelper.READ_TIMEOUT = 60

        while True:
            try:
                bot.polling(non_stop=False, timeout=30, long_polling_timeout=30, none_stop=True)
            except KeyboardInterrupt:
                print("Stopped by user")
                sys.exit(0)
            except Exception:
                time.sleep(10)
                continue
