import telebot
from datetime import datetime
import pytz

TOKEN = 'توکن_ربات_تو_اینجا'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: 'ساعتچند' in message.text)
def send_time(message):
    iran_time = datetime.now(pytz.timezone('Asia/Tehran')).strftime('%H:%M')
    bot.reply_to(message, f'🕒 ساعت هست {iran_time}')

bot.polling()
