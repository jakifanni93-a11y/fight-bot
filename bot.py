import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ["SPAM_BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])

allowed_users = set()
user_log = {}
waiting_for_sender = {}
waiting_for_custom = {}
active_fights = {}
fight_count = {}
MAX_FIGHTS = 5
fight_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.effective_chat.type != "private":
        return
    if user_id in waiting_for_sender:
        target, group_chat_id, _ = waiting_for_sender[user_id]
        await update.message.reply_text(
            f"\u2694\uFE0F Target: *{target}*\n\nApna naam bhej:",
            parse_mode="Markdown"
        )
        return
    await update.message.reply_text(
        "\U0001F4E2\u2694\uFE0F *SPAM BOT — BY RACHIT X RUCHIKA*\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "*USE KAISE KARE:*\n\n"
        "1\uFE0F\u20E3 Bot ko group mein add karo\n"
        "2\uFE0F\u20E3 Bot ko *Admin* banao\n"
        "3\uFE0F\u20E3 Group mein: `/fight @target`\n"
        "4\uFE0F\u20E3 DM aayega — naam batao — spam shuru!\n"
        "5\uFE0F\u20E3 Band karne ke liye: `/stop`\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "\u26A0\uFE0F 5 fights free — phir @ruchika\_owns se lo\n"
        "━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("\U0001F511 PERMISSION LO", url="https://t.me/ruchika_owns")
        ]])
    )

async def allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    user_id = None
    name = None
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        name = update.message.reply_to_message.from_user.first_name
    elif update.message.entities:
        for entity in update.message.entities:
            if entity.type == "text_mention":
                user_id = entity.user.id
                name = entity.user.first_name
                break
    if user_id:
        allowed_users.add(user_id)
        fight_count[user_id] = 0
        await update.message.reply_text(f"\u2705 {name} BKL AAGYA PERMISSION!")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="\u2705 *PERMISSION MIL GAYI!*\n\nGroup mein ja aur `/fight @target` likh!\n\U0001F525 5 fights free",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    else:
        await update.message.reply_text("\u274c KISI KO REPLY KAR YA MENTION KAR!")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    user_id = None
    name = None
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        name = update.message.reply_to_message.from_user.first_name
    elif update.message.entities:
        for entity in update.message.entities:
            if entity.type == "text_mention":
                user_id = entity.user.id
                name = entity.user.first_name
                break
    if user_id and user_id in allowed_users:
        allowed_users.remove(user_id)
        await update.message.reply_text(f"\u274c {name} HATA DIYA!")
    else:
        await update.message.reply_text("YE TO ALLOWED HI NAHI THA!")

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not user_log:
        await update.message.reply_text("Kisi ne use nahi kiya abhi.")
        return
    msg = "\U0001F4CB *USERS:*\n\n"
    for uid, cid in user_log.items():
        msg += f"User: `{uid}` | Chat: `{cid}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_fights:
        active_fights.pop(user_id)
        await update.message.reply_text("\U0001F6D1 SPAM KHATAM!")

async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_private = update.effective_chat.type == "private"

    if is_private:
        await update.message.reply_text(
            "\u26A0\uFE0F *PEHLE BOT KO GROUP MEIN ADD KAR!*",
            parse_mode="Markdown"
        )
        return

    if user_id != OWNER_ID and user_id not in allowed_users:
        if fight_count.get(user_id, 0) >= MAX_FIGHTS:
            await update.message.reply_text("\u26D4 TERI 5 FIGHTS KHATAM! @ruchika\_owns SE PERMISSION LE", parse_mode="Markdown")
            return

    if user_id in active_fights:
        await update.message.reply_text("\u26A0\uFE0F PAHLE /stop KAR!")
        return

    target = None
    if context.args:
        target = " ".join(context.args)
    if not target:
        await update.message.reply_text("\u274c Use: /fight @TargetName")
        return

    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await update.message.reply_text("\u26A0\uFE0F *MUJHE ADMIN BANAO PEHLE!*", parse_mode="Markdown")
            return
    except Exception:
        await update.message.reply_text("\u26A0\uFE0F *MUJHE ADMIN BANAO PEHLE!*", parse_mode="Markdown")
        return

    user_log[user_id] = chat_id
    if user_id != OWNER_ID:
        count = fight_count.get(user_id, 0)
        if count >= MAX_FIGHTS:
            await update.message.reply_text("\u26D4 TERI 5 FIGHTS KHATAM! @ruchika\_owns SE PERMISSION LE", parse_mode="Markdown")
            return
        fight_count[user_id] = count + 1

    waiting_for_sender[user_id] = (target, chat_id, update.message.message_id)
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(
        "\U0001F4AC DM KAR SETTING SET KAR \U0001F447",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("\U0001F4AC DM KARO", url=f"https://t.me/{bot_username}?start=setup")
        ]])
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_private = update.effective_chat.type == "private"

    if user_id in waiting_for_custom:
        sender, target, group_chat_id = waiting_for_custom.pop(user_id)
        custom_text = update.message.text.strip()
        active_fights[user_id] = True
        await update.message.reply_text("\U0001F525 SPAM SHURU! Group dekh ja!")
        asyncio.create_task(run_spam(context, [custom_text], user_id, group_chat_id))
        return

    if not is_private:
        return

    if user_id not in waiting_for_sender:
        await update.message.reply_text("Pehle group mein `/fight @target` likh!", parse_mode="Markdown")
        return

    sender = update.message.text.strip()
    target, group_chat_id, _ = waiting_for_sender.pop(user_id)
    fight_data[user_id] = (sender, target, group_chat_id)

    keyboard = [
        [InlineKeyboardButton("1\uFE0F\u20E3 FIGHT MESSAGES", callback_data=f"fight|{user_id}")],
        [InlineKeyboardButton("2\uFE0F\u20E3 APNA TEXT DAL", callback_data=f"custom|{user_id}")],
    ]
    await update.message.reply_text(
        f"\u2694\uFE0F *{sender}* vs *{target}*\n\nKaunsa spam?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    action = data[0]
    user_id = int(data[1])

    if user_id not in fight_data:
        await query.edit_message_text("\u274c Dobara /fight karo group mein.")
        return

    sender, target, group_chat_id = fight_data[user_id]

    if action == "custom":
        waiting_for_custom[user_id] = (sender, target, group_chat_id)
        await query.edit_message_text("\u270D\uFE0F APNA TEXT BHEJ:")
        return

    if action == "fight":
        active_fights[user_id] = True
        await query.edit_message_text("\U0001F525 SPAM SHURU! `/stop` se band karo.")
        blood = "\U0001FA78"
        fire = "\U0001F525"
        hot = "\U0001F975"
        lol = "\U0001F923"
        puke = "\U0001F922\U0001F92E"
        messages = [
            f"{target} TERI MAA KA PEROID {blood*10}",
            f"{sender} PAPA ON FIRE {fire*10}",
            f"{sender} fuck by {target} {hot*10}",
            f"{target} TERI MA KE NUDES KO VPS EDIT BANA DU? {lol*10}",
            f"{target} TERI MAA KI CHUT SE BADBU ARHI HE CHUT KESE MARU USKI {puke}",
            f"{target} TERI MAA KA PEROID {blood*10}",
            f"{sender} PAPA ON FIRE {fire*10}",
            f"{sender} fuck by {target} {hot*10}",
            f"{target} TERI MA KE NUDES KO VPS EDIT BANA DU? {lol*10}",
            f"{target} TERI MAA KI CHUT SE BADBU ARHI HE CHUT KESE MARU USKI {puke}",
        ]
        asyncio.create_task(run_spam(context, messages, user_id, group_chat_id))

async def run_spam(context, messages, user_id, group_chat_id):
    while user_id in active_fights:
        msg = "\n\n\n\n".join(messages)
        try:
            await context.bot.send_message(chat_id=group_chat_id, text=msg)
        except Exception:
            pass
        await asyncio.sleep(0.02)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in waiting_for_sender or user_id in waiting_for_custom:
        return
    await update.message.reply_text("OWNER SE BAT KAR KE AA @ruchika_owns")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("allow", allow))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("fight", fight))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("\u2705 Spam Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
