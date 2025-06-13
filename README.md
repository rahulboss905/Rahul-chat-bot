# Telegram Contact & Broadcast Bot

A simple yet powerful Telegram bot that lets people contact you privately, supports
broadcasts to users and/or groups, keeps basic statistics, and allows the owner to
customise the welcome message.

## Features
* **Contact Forwarding** – Every private message sent to the bot is forwarded to the owner.  
  The owner can reply with `/reply <user_id> <message>`.
* **Custom Welcome** – `/setwelcome Your message` sets the welcome text users see on `/start`.
* **Broadcasts** – `/broadcast` lets the owner choose to send a message to **Users**, **Groups**, or **Everyone**.  
* **Statistics** – `/stats` shows counts of registered users and groups.
* **SQLite Storage** – Persists chats and welcome messages between restarts.

## Setup

1. **Create a Bot** with @BotFather, grab the token.
2. **Find your numeric Telegram user‑id**, e.g. via @userinfobot.
3. `git clone` or unzip this repo, then
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Edit `main.py` and replace  
   ```python
   BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
   OWNER_ID = 123456789
   ```
5. Run the bot:
   ```bash
   python main.py
   ```

## Commands (Owner Only)
| Command | Purpose |
|---------|---------|
| `/broadcast` | Start the broadcast wizard |
| `/setwelcome <text>` | Change `/start` welcome text |
| `/stats` | Show number of users & groups |
| `/reply <user_id> <text>` | Reply to a user |

## Deploying
The bot runs fine on any server or platform that supports long‑polling: Railway, Heroku, Fly.io, etc.
Replace `application.run_polling()` with webhook logic if you need webhooks.

---

Made with ❤️ using [python‑telegram‑bot](https://github.com/python-telegram-bot/python-telegram-bot).