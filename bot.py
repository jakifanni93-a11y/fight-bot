import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])

allowed_users = set()
user_log = {}
waiting_for_sender = {}   # {user_id: (target, group_chat_id, group_message_id)}
waiting_for_custom = {}   # {user_id: (sender, target, group_chat_id)}
active_fights = {}        # {user_id: True}
fight_data = {}           # {user_id: (sender, target, group_chat_id)}

# =============================================
# OWNER COMMANDS
# =============================================

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
        await update.message.reply_text(f"\u2705 {name} BKL AAGYA PERMISSION!")
    else:
        await update.message.reply_text("\u274c GAWAR KISI KO MANTION TO KAR!!!")

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
        await update.message.reply_text(f"\u274c {name} JA PHIR SE PERMISSION LEKE AA! @ruchika_owns")
    else:
        await update.message.reply_text("TUJE TO KABHI DEKHA NAI JA PERMISSION LEKE AA @ruchika_owns")

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not user_log:
        await update.message.reply_text("Abhi kisi ne use nahi kiya.")
        return
    msg = "\U0001F4CB Fight use karne wale:\n\n"
    for uid, cid in user_log.items():
        msg += f"User ID: `{uid}` | Chat ID: `{cid}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# =============================================
# STOP COMMAND — GROUP MEIN
# =============================================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_fights:
        active_fights.pop(user_id)
        await update.message.reply_text("\U0001F6D1 CHUDAI KHATAM!!!!! KHUSH HO JA CHUDAI KHATAM KAR DI TUNE")
    else:
        await update.message.reply_text("KOI CHUDEGA?")

# =============================================
# FIGHT COMMAND — GROUP MEIN
# =============================================

async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_private = update.effective_chat.type == "private"

    if user_id != OWNER_ID and user_id not in allowed_users:
        await update.message.reply_text("\u26D4 NIKAL PERMISSION LEKE AA PAHLE @ruchika_owns")
        return

    if user_id in active_fights:
        await update.message.reply_text("\u26A0\uFE0F PAHLE STOP TO KAR BKL!")
        return

    target = None
    if context.args:
        target = " ".join(context.args)

    if not target:
        await update.message.reply_text("\u274c Use: /fight @TargetName")
        return

    # Group mein command aayi
    if not is_private:
        user_log[user_id] = chat_id
        waiting_for_sender[user_id] = (target, chat_id, update.message.message_id)

        bot_username = (await context.bot.get_me()).username
        keyboard = [[InlineKeyboardButton(
            "\U0001F4AC DM KARO — SETTING SET KARO",
            url=f"https://t.me/{bot_username}?start=setup"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"\u26A0\uFE0F DM KAR BKL SETTING SET KAR PAHLE TARGET KA \U0001F447",
            reply_markup=reply_markup
        )
        return

    # Private mein /fight — seedha kaam karo
    waiting_for_sender[user_id] = (target, chat_id, update.message.message_id)
    await update.message.reply_text(
        f"\u2694\uFE0F Target: *{target}*\n\nNAME BOL JALDI SE APNA:",
        parse_mode="Markdown"
    )

# =============================================
# /START — PRIVATE MEIN AAYA MATLAB GROUP SE REDIRECT HUA
# =============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_private = update.effective_chat.type == "private"

    if not is_private:
        return

    if user_id in waiting_for_sender:
        target, group_chat_id, _ = waiting_for_sender[user_id]
        await update.message.reply_text(
            f"\u2694\uFE0F Target: *{target}*\n\nNAME BOL JALDI SE APNA:",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Pehle group mein /fight @target likh ke aa!"
        )

# =============================================
# PRIVATE MESSAGE HANDLE — NAAM LENA → MENU
# =============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_private = update.effective_chat.type == "private"

    # Custom text wait — private mein
    if user_id in waiting_for_custom:
        sender, target, group_chat_id = waiting_for_custom.pop(user_id)
        custom_text = update.message.text.strip()
        active_fights[user_id] = True
        await update.message.reply_text("\U0001F525 SPAM SHURU GROUP MEIN! /stop se band karo.")
        asyncio.create_task(run_custom_fight(context, custom_text, user_id, group_chat_id))
        return

    # Sirf private mein naam lo
    if not is_private:
        if user_id not in waiting_for_sender:
            await update.message.reply_text("DM KAR BKL \U0001F4AC PEHLE /fight @target likh")
        return

    if user_id not in waiting_for_sender:
        await update.message.reply_text("Pehle group mein /fight @target likh ke aa!")
        return

    sender = update.message.text.strip()
    target, group_chat_id, _ = waiting_for_sender.pop(user_id)
    fight_data[user_id] = (sender, target, group_chat_id)

    keyboard = [
        [InlineKeyboardButton("1\uFE0F\u20E3 SHORT TEXT FIGHT", callback_data=f"short|{user_id}")],
        [InlineKeyboardButton("2\uFE0F\u20E3 LONG TEXT FIGHT", callback_data=f"long|{user_id}")],
        [InlineKeyboardButton("3\uFE0F\u20E3 KHUD DAL LE TEXT", callback_data=f"custom|{user_id}")],
        [InlineKeyboardButton("4\uFE0F\u20E3 GAALI - FULL READY HU", callback_data=f"gaali|{user_id}")],
        [InlineKeyboardButton("5\uFE0F\u20E3 ROAST - AAJA", callback_data=f"roast|{user_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"\u2694\uFE0F *{sender}* vs *{target}*\n\nKaunsa mode chahiye?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# =============================================
# BUTTON PRESS — PRIVATE MEIN
# =============================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    spam_type = data[0]
    user_id = int(data[1])

    if user_id not in fight_data:
        await query.edit_message_text("\u274c Fight data nahi mila, dobara /fight karo group mein.")
        return

    sender, target, group_chat_id = fight_data[user_id]

    if spam_type == "custom":
        waiting_for_custom[user_id] = (sender, target, group_chat_id)
        await query.edit_message_text("\u270D\uFE0F Apna custom text bhejo private mein — woh group mein spam hoga:")
        return

    active_fights[user_id] = True
    await query.edit_message_text(f"\U0001F525 SPAM SHURU GROUP MEIN! /stop se band karo.")
    asyncio.create_task(run_fight(context, sender, target, user_id, spam_type, group_chat_id))

# =============================================
# FIGHT MESSAGES
# =============================================

async def run_fight(context, sender, target, user_id, spam_type, group_chat_id):
    blood = "\U0001FA78"
    fire = "\U0001F525"
    hot = "\U0001F975"
    lol = "\U0001F923"
    puke = "\U0001F922\U0001F92E"
    angry = "\U0001F621"
    skull = "\U0001F480"
    clown = "\U0001F921"

    if spam_type == "short":
        messages = [
            f"{target} TERI MAA KA PEROID {blood*5}",
            f"{sender} PAPA ON FIRE {fire*5}",
            f"{sender} fuck by {target} {hot*5}",
            f"{target} TERI MA KE NUDES {lol*5}",
            f"{target} TERI MAA KI CHUT {puke}",
        ]
    elif spam_type == "long":
        messages = [
            f"created by RACHIT X RUCHIKA",
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
            f"{target} TERI MAA KA PEROID {blood*10}",
            f"{sender} PAPA ON FIRE {fire*10}",
            f"{sender} fuck by {target} {hot*10}",
            f"{target} TERI MA KE NUDES KO VPS EDIT BANA DU? {lol*10}",
            f"{target} TERI MAA KI CHUT SE BADBU ARHI HE CHUT KESE MARU USKI {puke}",
            f"created by RACHIT X RUCHIKA",
        ]
    elif spam_type == "gaali":
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
            f"{target} TERI MAA KA PEROID {blood*10}",
            f"{sender} PAPA ON FIRE {fire*10}",
            f"{sender} fuck by {target} {hot*10}",
            f"{target} TERI MA KE NUDES KO VPS EDIT BANA DU? {lol*10}",
            f"{target} TERI MAA KI CHUT SE BADBU ARHI HE CHUT KESE MARU USKI {puke}",
        ]
    elif spam_type == "roast":
        messages = [
            f"{clown*5} {target} sun bhai, tere jaisa insaan duniya mein dobara nahi banega — THANK GOD {clown*5}",
            f"{skull*3} {target} ki life ek joke hai aur punchline bhi nahi hai {skull*3}",
            f"{angry*5} {target} tere baap ne socha tha tu kuch karega — ab woh raat ko rota hai {angry*5}",
            f"{lol*5} {target} itna useless hai ke Google bhi tera naam suggest nahi karta {lol*5}",
            f"{puke} {target} tere kapde utaar ke bhi koi nahi dekhega — free mein bhi nahi {puke}",
            f"{clown*5} {target} teri aukaat? Zero. Teri value? Minus. Tera future? {skull} {clown*5}",
            f"{angry*5} {target} tune jo socha tha woh kabhi nahi hoga — {sender} ne prove kar diya {angry*5}",
            f"{lol*5} {target} itna ghatiya hai ke tere friends bhi fake hain {lol*5}",
            f"{skull*3} {target} ek kaam dhang se kar nahi sakta — aur lad raha hai {sender} se {skull*3}",
            f"{puke} {target} tujhe dekh ke lagta hai evolution galti kar gaya {puke}",
            f"{clown*5} {target} teri maa ne socha tha tu hero banega — ab {sender} hero hai {clown*5}",
            f"{angry*5} {target} band kar apni bakwaas — {sender} tujhse 100 guna better hai {angry*5}",
            f"{lol*5} {target} tere sapne bhi tujhe seriously nahi lete {lol*5}",
            f"{skull*3} {target} duniya mein agar uselessness ka award hota to tu first aata {skull*3}",
            f"{puke} {target} NIKAL YAHAN SE — {sender} ka time waste mat kar {puke}",
        ]
    else:
        messages = [f"{target} TERI MAA KA PEROID {blood*10}"]

    while user_id in active_fights:
        msg = "\n\n\n\n".join(messages)
        try:
            await context.bot.send_message(chat_id=group_chat_id, text=msg)
        except Exception:
            break
        await asyncio.sleep(0.02)

async def run_custom_fight(context, custom_text, user_id, group_chat_id):
    while user_id in active_fights:
        try:
            await context.bot.send_message(chat_id=group_chat_id, text=custom_text)
        except Exception:
            break
        await asyncio.sleep(0.02)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in waiting_for_sender or user_id in waiting_for_custom:
        return
    await update.message.reply_text("JA @ruchika_owns SE PERMISSION LEKE AA")

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
    print("\u2705 Fight Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
