import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])

# Allowed users list
allowed_users = set()

# Fight wait list: {user_id: target_name}
waiting_for_sender = {}

# Active fights: {user_id: True}
active_fights = {}

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
        await update.message.reply_text(f"✅ {name} ko permission de di gayi!")
    else:
        await update.message.reply_text("❌ Kisi ko reply karo ya mention karo.")


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
        await update.message.reply_text(f"❌ {name} ki permission hata di!")
    else:
        await update.message.reply_text("Ye user allowed nahi tha.")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_fights:
        active_fights.pop(user_id)
        await update.message.reply_text("\U0001F6D1 CHUDAI KHATAM")
    else:
        await update.message.reply_text("KOI CHUDEGA?.")


async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID and user_id not in allowed_users:
        await update.message.reply_text("\u26D4NIKAL PERMISSION LEKE AA PAHLE ")
        return
    if user_id in active_fights:
        await update.message.reply_text("\u26A0\uFE0F PAHLE STOP TO KAR BKL!")
        return
    target = None
    if context.args:
        target = " ".join(context.args)
    if not target:
        await update.message.reply_text("❌ Use: /fight @TargetName")
        return
    waiting_for_sender[user_id] = target
    await update.message.reply_text(
        f"\u2694\uFE0F Target: *{target}*\n\n NAME BOL JALDI SE :",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in waiting_for_sender:
        return
    sender = update.message.text.strip()
    target = waiting_for_sender.pop(user_id)
    active_fights[user_id] = True
    asyncio.create_task(run_fight(update, context, sender, target, user_id))


async def run_fight(update, context, sender, target, user_id):
    blood = "\U0001FA78"
    fire = "\U0001F525"
    hot = "\U0001F975"
    lol = "\U0001F923"
    puke = "\U0001F922\U0001F92E"
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

    
    while user_id in active_fights:
        msg = "\n\n\n\n".join(messages)
        try:
            await update.message.reply_text(msg)
        except Exception:
            break
        await asyncio.sleep(0.02)
   


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("allow", allow))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("fight", fight))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Fight Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
