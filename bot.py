import telebot
from datetime import datetime
import pytz

TOKEN = '7918766042:AAFt9GdXQFZyenehu5b0C-eAqX860nwQRmk'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: 'ساعتچند' in message.text)
def send_time(message):
    iran_time = datetime.now(pytz.timezone('Asia/Tehran')).strftime('%H:%M')
    bot.reply_to(message, f'🕒 ساعت هست {iran_time}')

bot.polling()
