#!/usr/bin/env python3

import telebot
import config
from requests import exceptions
from time import sleep
from os import remove
from sys import argv

with open(argv[1][:-3] + "_token") as token:
    TOKEN = token.read().strip()
dummy = telebot.TeleBot(TOKEN)

@dummy.message_handler(content_types=["text"])
def answerer(message):
    for id in config.developers:
        dummy.forward_message(id, message.chat.id, message.message_id)
    dummy.reply_to(message, "Извините, это сообщение вызвало какую-то ошибку. Пожалуйста, воздержитесь от повторения данной команды в ближайшее время. Разработчик уже оповещен о данной проблеме")
    exit(0)

if __name__ == '__main__':
    dummy.polling(none_stop = False)
    
