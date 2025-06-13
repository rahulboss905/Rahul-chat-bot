import logging
import sqlite3
from pathlib import Path
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
import asyncio
import os

# Configuration
BOT_TOKEN = "7902308716:AAG1FBzEafazIDVO_xRc5fTsXEU4PqUcO9k"
OWNER_ID = 7456681709
DB_PATH = Path("bot.db")

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY,
        chat_type TEXT,
        title TEXT,
        username TEXT,
        first_name TEXT,
        last_name TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS welcome (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        message TEXT)""")
    cur.execute("INSERT OR IGNORE INTO welcome (id, message) VALUES (1, 'ðŸ‘‹ Hi! Welcome to the bot.')")
    conn.commit()
    conn.close()

def add_chat(chat: Chat):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""INSERT OR REPLACE INTO chats (chat_id, chat_type, title, username, first_name, last_name)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (chat.id, chat.type, getattr(chat, "title", None), getattr(chat, "username", None),
         getattr(chat, "first_name", None), getattr(chat, "last_name", None)))
    conn.commit()
    conn.close()

def get_welcome():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT message FROM welcome WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "ðŸ‘‹ Hi!"

def set_welcome(text):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE welcome SET message=? WHERE id=1", (text,))
    conn.commit()
    conn.close()

def get_chat_ids(chat_type_filter=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if chat_type_filter == "private":
        cur.execute("SELECT chat_id FROM chats WHERE chat_type='private'")
    elif chat_type_filter == "group":
        cur.execute("SELECT chat_id FROM chats WHERE chat_type!='private'")
    else:
        cur.execute("SELECT chat_id FROM chats")
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids

def stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chats WHERE chat_type='private'")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM chats WHERE chat_type!='private'")
    groups = cur.fetchone()[0]
    conn.close()
    return {"users": users, "groups": groups}

# Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat
    user = update.effective_user
    add_chat(chat)
    welcome_template = get_welcome()
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    username = f"@{user.username}" if user.username else mention
    fullname = f"{user.first_name} {user.last_name or ''}".strip()
    welcome = (welcome_template
               .replace("{first}", user.first_name or "")
               .replace("{last}", user.last_name or "")
               .replace("{fullname}", fullname)
               .replace("{username}", username)
               .replace("{mention}", mention)
               .replace("{id}", str(user.id)))
    await update.message.reply_text(welcome, parse_mode=constants.ParseMode.MARKDOWN)

async def set_welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Usage: /setwelcome <your welcome message>")
        return
    set_welcome(msg)
    await update.message.reply_text("âœ… Welcome updated.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    help_text = """ðŸ›  *Bot Owner Commands:*
/setwelcome <msg> â€“ Set welcome message
/broadcast â€“ Broadcast message to users/groups
/stats â€“ Show user and group count
/help â€“ Show this help message"""
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.MARKDOWN)

async def broadcast_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    kb = [[InlineKeyboardButton("Users", callback_data="private"),
           InlineKeyboardButton("Groups", callback_data="group")],
          [InlineKeyboardButton("All", callback_data="all")]]
    await update.message.reply_text("Choose target:", reply_markup=InlineKeyboardMarkup(kb))
    return 0

async def broadcast_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["target"] = query.data
    await query.edit_message_text("Now send the message to broadcast.")
    return 1

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("target", "all")
    ids = get_chat_ids(target if target in ["private", "group"] else None)
    success = 0
    for cid in ids:
        try:
            await update.message.copy(cid)
            success += 1
        except:
            continue
    await update.message.reply_text(f"âœ… Broadcast done: {success} sent.")
    return -1

async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return -1

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    s = stats()
    await update.message.reply_text(f"ðŸ“Š Users: {s['users']}
Groups: {s['groups']}")

async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat
    add_chat(chat)
    if chat.id == OWNER_ID:
        return
    text = update.message.text or ""
    formatted = f"âœ‰ï¸ Message from {chat.first_name} ({chat.id}):\n{text}"
    await context.bot.send_message(chat_id=OWNER_ID, text=formatted)

async def reply_to_owner_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        orig = update.message.reply_to_message.text
        if orig.startswith("âœ‰ï¸ Message from") and "(" in orig:
            try:
                uid = int(orig.split("(")[1].split(")")[0])
                await context.bot.send_message(chat_id=uid, text=update.message.text)
                await update.message.reply_text("âœ… Sent.")
            except Exception as e:
                await update.message.reply_text(f"âŒ Failed: {e}")

# Create Telegram Application
init_db()
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("setwelcome", set_welcome_cmd))
application.add_handler(CommandHandler("stats", stats_cmd))
application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("broadcast", broadcast_entry)],
    states={0: [CallbackQueryHandler(broadcast_choose)],
            1: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_send)]},
    fallbacks=[CommandHandler("cancel", broadcast_cancel)],
))
application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, reply_to_owner_handler))
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_handler))

# Flask webhook routes
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def telegram_webhook():
    data = request.get_data().decode("utf-8")
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is alive!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    webhook_url = f"https://rahul-chat-bot.onrender.com/{BOT_TOKEN}"
    asyncio.run(application.bot.set_webhook(url=webhook_url))
    app.run(host="0.0.0.0", port=port)
