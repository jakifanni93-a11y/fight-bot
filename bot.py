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

# Active fights: {user_id: True} — /stop se band hoga
active_fights = {}

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


# =============================================
# STOP COMMAND
# =============================================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_fights:
        active_fights.pop(user_id)
        await update.message.reply_text("🛑 Fight band kar di gayi!")
    else:
        await update.message.reply_text("Koi fight chal nahi rahi.")


# =============================================
# FIGHT COMMAND
# =============================================

async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID and user_id not in allowed_users:
        await update.message.reply_text("⛔ Tumhe permission nahi hai.")
        return

    if user_id in active_fights:
        await update.message.reply_text("⚠️ Pehle /stop karo, fight already chal rahi hai!")
        return

    target = None
    if context.args:
        target = " ".join(context.args).lstrip("@")

    if not target:
        await update.message.reply_text("❌ Use: /fight @TargetName")
        return

    waiting_for_sender[user_id] = target
    await update.message.reply_text(
        f"⚔️ Target: *{target}*\n\nAb apna naam bhejo:",
        parse_mode="Markdown"
    )


# =============================================
# SENDER NAAM LENA
# =============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in waiting_for_sender:
        return

    sender = update.message.text.strip()
    target = waiting_for_sender.pop(user_id)

    active_fights[user_id] = True
    await update.message.reply_text(f"⚔️ Fight shuru! /stop likhoge tab band hogi.")

    asyncio.create_task(run_fight(update, context, sender, target, user_id))


# =============================================
# FIGHT MESSAGES — YAHAN APNE MESSAGES DAALO
# {sender} aur {target} rakho, baaki apna text likho
# =============================================

async def run_fight(update, context, sender, target, user_id):
    messages = [
        f"⚔️ {sender} ne {target} ko challenge kiya!",
        f"🔥 {sender} ne attack kiya — {target} par 30 damage!",
        f"💥 {target} ne counter kiya — {sender} ghabra gaya!",
        f"🗡️ {sender} ka CRITICAL HIT — {target} par 50 damage!",
        f"🛡️ {target} ne shield lagaya lekin {sender} ne tod diya!",
        f"💀 {sender} ne {target} ko ek aur baar maara!",
        f"🔥 {target} ab bhi lad raha hai — {sender} hairan hai!",
        f"⚡ {sender} ka secret move — {target} par 80 damage!",
        f"😤 {target} ne last energy lagai — {sender} ko push kiya!",
        f"🏆 {sender} unbeatable hai — {target} haar maan le!",
    ]

    i = 0
    while user_id in active_fights:
        msg = messages[i % len(messages)]
        try:
            await update.message.reply_text(msg)
        except Exception:
            break
        await asyncio.sleep(0.3)  # ⚡ Speed — 0.5 second gap (kam karo aur fast hoga)
        i += 1

    if user_id not in active_fights:
        try:
            await update.message.reply_text(f"🛑 Fight khatam! {sender} vs {target} — over!")
        except Exception:
            pass


# =============================================
# MAIN
# =============================================

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
