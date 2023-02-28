import json
import os

import telebot
import websocket

# В качестве источника данных был выбран Binance WebSocket API,
# для подключения к которой используется библиотека websocket.
# Обработка данных и отправка сообщений происходят в функции
# on_message. В качестве интерфейса для приема уведомлений
# было решено использовать Telegram. Команда connect запускает
# отслеживание движений цены ETH, команды start и stop - для
# подписки на уведомления и отписки от них.

# эндпоинт исчтоника данных
ENDPOINT = 'wss://fstream.binance.com/ws/ethusdt@aggTrade'
SUBSCRIPTION_PAYLOAD = {'method': 'SUBSCRIBE', 'params': ['ethusdt@aggTrade'], 'id': 1}

bot = telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN'), parse_mode=None)

price = None
timestamp = None
connected = False

users = {
    'users': dict(),
}


def send_telegram_message(message):
    for user in users:
        if users[user]:
            bot.send_message(chat_id=user, text=message)


def on_message(ws, message):
    global price, timestamp

    message = json.loads(message)

    # извлекаем данные о цене и метке времени
    new_price = float(message['p'])
    new_timestamp = int(message['T']) // 1000

    # проверка на первое сообщение или изменение цены на 1% за последние 60 мин.
    if price is None:
        price = new_price
        timestamp = new_timestamp
    else:
        time_diff = new_timestamp - timestamp
        if time_diff >= 3600:
            percent_change = abs(new_price - price) / price * 100
            if percent_change >= 1:
                message = f"Стоимость ETH изменилась на {percent_change:.2f}% за последние 60 минут"
            else:
                message = f"Стоимость ETH не изменилась более чем на 1% за последние 60 минут"
            send_telegram_message(message)

            price = new_price
            timestamp = new_timestamp


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Вы подписаны на отправку уведомлений об изменении цены ETH')
    users[message.from_user.id] = True


@bot.message_handler(commands=['stop'])
def stop(message):
    bot.reply_to(message, 'Вы отписались от отправки уведомлений об изменении цены ETH')
    users[message.from_user.id] = False


# функция отслеживания через вебсокет запускается командой
@bot.message_handler(commands=['connect'])
def connect(message):
    global connected
    if not connected:
        bot.reply_to(message, 'Начинаю отслеживание движений цены ETH')
        connected = True
        ws = websocket.WebSocketApp(ENDPOINT, on_message=on_message)
        ws.on_open = lambda ws: ws.send(json.dumps(SUBSCRIPTION_PAYLOAD))
        ws.run_forever()
    else:
        bot.reply_to(message, 'Отслеживание движений цены ETH в процессе')


if __name__ == "__main__":
    bot.infinity_polling()
