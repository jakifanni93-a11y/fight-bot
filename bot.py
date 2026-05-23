import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["8307295317:AAF_mH-HrA0yr-q-SNGZHrgooTgUNt2zSBM"]
OWNER_ID = int(os.environ["8588629743"])

# Allowed users list
allowed_users = set()

# Fight wait list
waiting_for_sender = {}

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
# FIGHT COMMAND
# =============================================

async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID and user_id not in allowed_users:
        await update.message.reply_text("⛔ Tumhe permission nahi hai.")
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

    await run_fight(update, context, sender, target)


# =============================================
# FIGHT MESSAGES — YAHAN APNE MESSAGES DAALO
# Sirf {sender} aur {target} rakho, baaki text apna likho
# Jitne chahiye utne messages add karo
# =============================================

async def run_fight(update, context, sender, target):
    messages = [
        f"⚔️ {sender} ne {target} ko challenge kiya!",
        f"🔥 {sender} ne attack kiya — {target} par 30 damage!",
        f"💥 {target} ne counter kiya — {sender} ghabra gaya!",
        f"🗡️ {sender} ka CRITICAL HIT — {target} par 50 damage!",
        f"🛡️ {target} ne shield lagaya lekin {sender} ne tod diya!",
        f"💀 GAME OVER! {sender} ne {target} ko defeat kar diya! 🏆",
    ]

    for msg in messages:
        await update.message.reply_text(msg)
        await asyncio.sleep(2)


# =============================================
# MAIN
# =============================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("allow", allow))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("fight", fight))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Fight Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
