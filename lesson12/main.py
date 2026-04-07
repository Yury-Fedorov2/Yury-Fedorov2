import telebot
from config import BOT_TOKEN
from extensions import CurrencyConverter, APIException

bot = telebot.TeleBot(BOT_TOKEN)

AVAILABLE_CURRENCIES = ['доллар', 'евро', 'рубль']

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    welcome_text = (
        "🤖 Добро пожаловать в конвертер валют!\n\n"
        "Для конвертации валюты отправьте сообщение в формате:\n"
        "<валюта1> <валюта2> <количество>\n\n"
        "Пример: доллар евро 100\n\n"
        "Доступные валюты: доллар, евро, рубль\n\n"
        "Команды:\n"
        "/start, /help — показать эту справку\n"
        "/values — показать доступные валюты"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['values'])
def show_values(message):
    """Обработчик команды /values"""
    values_text = "💱 Доступные валюты:\n" + "\n".join(f"• {currency}" for currency in AVAILABLE_CURRENCIES)
    bot.reply_to(message, values_text)

@bot.message_handler(content_types=['text'])
def convert_currency(message):
    """Обработчик текстовых сообщений для конвертации валют"""
    try:
        parts = message.text.split()

        if len(parts) != 3:
            raise APIException('Неверный формат запроса. Используйте: <валюта1> <валюта2> <количество>')

        base, quote, amount_str = parts

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise APIException('Количество должно быть положительным числом')
        except ValueError:
            raise APIException('Количество должно быть числом')

        result = CurrencyConverter.get_price(base, quote, amount)

        response_text = f'{amount} {base} = {result} {quote}'
        bot.reply_to(message, response_text)

    except APIException as e:
        bot.reply_to(message, f'Ошибка: {e}')
    except Exception as e:
        bot.reply_to(message, f'Неизвестная ошибка: {type(e).__name__}: {e}')

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)