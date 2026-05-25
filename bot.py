import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])

allowed_users = set()
user_log = {}
waiting_for_sender = {}
waiting_for_custom = {}
waiting_for_custom_name = {}
active_fights = {}
fight_count = {}
MAX_FIGHTS = 5
fight_data = {}

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
        return

    welcome = (
        "\U0001F480\u2694\uFE0F *FIGHT BOT — BY RACHIT X RUCHIKA* \u2694\uFE0F\U0001F480\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "\U0001F525 *YE BOT KYA KARTA HAI?*\n"
        "Kisi ko bhi group mein spam kar sakta hai — messages, gaaliyan, roast, name change sab!\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "\U0001F4CB *USE KARNE KE LIYE STEPS:*\n"
        "\n"
        "*STEP 1* — Owner se permission lo\n"
        "\u279C @ruchika\_owns ko message karo\n"
        "\n"
        "*STEP 2* — Bot ko group mein add karo\n"
        "\u279C Bot ko group mein add karo\n"
        "\u279C Bot ko *ADMIN* banao\n"
        "\u279C Admin mein *Change Group Info* ON karo\n"
        "\n"
        "*STEP 3* — Fight shuru karo\n"
        "\u279C Group mein: `/fight @TargetName`\n"
        "\u279C Bot bolega DM KAR — click karo\n"
        "\u279C Private mein naam batao\n"
        "\u279C Mode select karo aur spam shuru!\n"
        "\n"
        "*STEP 4* — Band karo\n"
        "\u279C Group mein `/stop` likho\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "\u26A0\uFE0F *5 fights free — uske baad dobara permission lo*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "\U0001F480 *AB JA AUR KISI KO BARBAD KAR!* \U0001F480"
    )

    keyboard = [[InlineKeyboardButton(
        "\U0001F511 PERMISSION LENE KE LIYE CLICK KARO",
        url="https://t.me/ruchika_owns"
    )]]
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
                text=(
                    "\u2705 *PERMISSION MIL GAYI!*\n\n"
                    "Ab group mein ja aur `/fight @target` likh!\n"
                    "\U0001F525 5 fights free hain tere liye"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
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

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_fights:
        active_fights.pop(user_id)
        await update.message.reply_text("\U0001F6D1 CHUDAI KHATAM!!!!! KHUSH HO JA CHUDAI KHATAM KAR DI TUNE")

async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    is_private = chat_type == "private"

    # Private mein /fight — group mein add karne bol
    if is_private:
        bot_username = (await context.bot.get_me()).username
        await update.message.reply_text(
            "\u26A0\uFE0F *PEHLE BOT KO GROUP MEIN ADD KAR!*\n\n"
            "1\uFE0F\u20E3 Apne group mein bot add karo\n"
            "2\uFE0F\u20E3 Bot ko *Admin* banao\n"
            "3\uFE0F\u20E3 Group mein ja aur `/fight @target` likh",
            parse_mode="Markdown"
        )
        return

    # Permission check
    if user_id != OWNER_ID and user_id not in allowed_users:
        count = fight_count.get(user_id, 0)
        if count >= MAX_FIGHTS:
            await update.message.reply_text(
                "\u26D4 *TERI 5 FIGHTS KHATAM!*\n\n@ruchika\_owns se dobara permission le",
                parse_mode="Markdown"
            )
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

    # Check bot admin hai ya nahi
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        is_admin = bot_member.status in ["administrator", "creator"]
    except Exception:
        is_admin = False

    if not is_admin:
        await update.message.reply_text(
            "\u26A0\uFE0F *BOT KO ADMIN BANAO!*\n\n"
            "Mujhe admin bana de group ka tabhi kaam karunga \U0001F608\n\n"
            "_Admin mein 'Change Group Info' permission ON karna mat bhulio_",
            parse_mode="Markdown"
        )
        return

    # Sab sahi hai — fight shuru
    user_log[user_id] = chat_id
    if user_id != OWNER_ID:
        count = fight_count.get(user_id, 0)
        if count >= MAX_FIGHTS:
            await update.message.reply_text(
                "\u26D4 *TERI 5 FIGHTS KHATAM!*\n\n@ruchika\_owns se dobara permission le",
                parse_mode="Markdown"
            )
            return
        fight_count[user_id] = count + 1

    waiting_for_sender[user_id] = (target, chat_id, update.message.message_id)
    bot_username = (await context.bot.get_me()).username
    keyboard = [[InlineKeyboardButton(
        "\U0001F4AC DM KARO — SETTING SET KARO",
        url=f"https://t.me/{bot_username}?start=setup"
    )]]
    await update.message.reply_text(
        "\u26A0\uFE0F DM KAR BKL SETTING SET KAR PAHLE \U0001F447",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_private = update.effective_chat.type == "private"

    if user_id in waiting_for_custom:
        sender, target, group_chat_id = waiting_for_custom.pop(user_id)
        custom_text = update.message.text.strip()
        active_fights[user_id] = True
        await update.message.reply_text("\U0001F525 JA KE GROUP DEKH")
        asyncio.create_task(run_custom_fight(context, custom_text, user_id, group_chat_id))
        return

    if user_id in waiting_for_custom_name:
        sender, target, group_chat_id = waiting_for_custom_name.pop(user_id)
        custom_names_text = update.message.text.strip()
        custom_names = [n.strip() for n in custom_names_text.split("\n") if n.strip()]
        if not custom_names:
            await update.message.reply_text("Kuch to likh bhai!")
            waiting_for_custom_name[user_id] = (sender, target, group_chat_id)
            return
        active_fights[user_id] = True
        await update.message.reply_text("\U0001F525 JA KE GROUP DEKH NAME CHANGE HO RAHA!")
        asyncio.create_task(run_name_change(context, custom_names, user_id, group_chat_id))
        return

    if not is_private:
        return

    if user_id not in waiting_for_sender:
        await update.message.reply_text(
            "Pehle group mein `/fight @target` likh ke aa!",
            parse_mode="Markdown"
        )
        return

    sender = update.message.text.strip()
    target, group_chat_id, _ = waiting_for_sender.pop(user_id)
    fight_data[user_id] = (sender, target, group_chat_id)

    keyboard = [
        [InlineKeyboardButton("1\uFE0F\u20E3 CHAT SPAM", callback_data=f"mainmenu_chat|{user_id}")],
        [InlineKeyboardButton("2\uFE0F\u20E3 NAME CHANGE SPAM", callback_data=f"mainmenu_name|{user_id}")],
        [InlineKeyboardButton("3\uFE0F\u20E3 STICKERS \U0001F6A7", callback_data=f"mainmenu_sticker|{user_id}")],
    ]
    await update.message.reply_text(
        f"\u2694\uFE0F *{sender}* vs *{target}*\n\nKYA KARNA HAI?",
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
        await query.edit_message_text("\u274c Fight data nahi mila, dobara /fight karo group mein.")
        return

    sender, target, group_chat_id = fight_data[user_id]

    if action == "mainmenu_chat":
        keyboard = [
            [InlineKeyboardButton("1\uFE0F\u20E3 SHORT TEXT", callback_data=f"short|{user_id}")],
            [InlineKeyboardButton("2\uFE0F\u20E3 LONG TEXT", callback_data=f"long|{user_id}")],
            [InlineKeyboardButton("3\uFE0F\u20E3 KHUD DAL LE TEXT", callback_data=f"custom|{user_id}")],
            [InlineKeyboardButton("4\uFE0F\u20E3 GAALI \U0001FA78", callback_data=f"gaali|{user_id}")],
            [InlineKeyboardButton("5\uFE0F\u20E3 ROAST \U0001F525", callback_data=f"roast|{user_id}")],
        ]
        await query.edit_message_text(
            "\U0001F4AC *CHAT SPAM MODE*\n\nKaunsa type chahiye?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    if action == "mainmenu_name":
        keyboard = [
            [InlineKeyboardButton("1\uFE0F\u20E3 AUTO NAMES", callback_data=f"nameauto|{user_id}")],
            [InlineKeyboardButton("2\uFE0F\u20E3 KHUD DEGA NAMES", callback_data=f"namecustom|{user_id}")],
        ]
        await query.edit_message_text(
            "\U0001F4DD *NAME CHANGE MODE*\n\nKaunsa type chahiye?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    if action == "mainmenu_sticker":
        await query.edit_message_text("STICKERS COMING SOON! \U0001F6A7")
        return

    if action == "nameauto":
        active_fights[user_id] = True
        await query.edit_message_text("\U0001F525 NAME CHANGE SHURU! Group mein `/stop` se band karo.")
        names = [
            f"{target} TERI MAA KA PEROID",
            f"{target} TERI MA KE NUDES KO VPS EDIT BANA DU?",
            f"{target} TERI MAA KA PEROID",
            f"{target} TERI MA KE NUDES KO VPS EDIT BANA DU?",
        ]
        asyncio.create_task(run_name_change(context, names, user_id, group_chat_id))
        return

    if action == "namecustom":
        waiting_for_custom_name[user_id] = (sender, target, group_chat_id)
        await query.edit_message_text(
            "\u270D\uFE0F *HAR LINE PE EK NAAM BHEJ:*\n\nExample:\nRAHUL PAGAL HAI\nRAHUL BHAAG",
            parse_mode="Markdown"
        )
        return

    if action == "custom":
        waiting_for_custom[user_id] = (sender, target, group_chat_id)
        await query.edit_message_text("\u270D\uFE0F APNA TEXT BHEJ — WOH BAR BAR SPAM HOGA:")
        return

    active_fights[user_id] = True
    await query.edit_message_text("\U0001F525 SPAM SHURU! Group mein `/stop` se band karo.")
    asyncio.create_task(run_fight(context, sender, target, user_id, action, group_chat_id))

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
            pass
        await asyncio.sleep(0.02)

async def run_name_change(context, names, user_id, group_chat_id):
    i = 0
    while user_id in active_fights:
        try:
            await context.bot.set_chat_title(chat_id=group_chat_id, title=names[i % len(names)])
        except Exception:
            pass
        await asyncio.sleep(0.01)
        i += 1

async def run_custom_fight(context, custom_text, user_id, group_chat_id):
    while user_id in active_fights:
        try:
            await context.bot.send_message(chat_id=group_chat_id, text=custom_text)
        except Exception:
            pass
        await asyncio.sleep(0.02)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in waiting_for_sender or user_id in waiting_for_custom or user_id in waiting_for_custom_name:
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
    print("\u2705 Fight Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
