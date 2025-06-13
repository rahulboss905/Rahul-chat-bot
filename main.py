from flask import Flask, request
import telebot
import os

API_TOKEN = '23888050:80679c77353535f9e13f10710a7feec9'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! Your bot is running on Render!")

@app.route(f"/{API_TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=['GET'])
def home():
    return "Bot is alive!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url=f"https://rahul-chat-bot.onrender.com/<your-actual-bot-token>")
    app.run(host="0.0.0.0", port=port)
  
