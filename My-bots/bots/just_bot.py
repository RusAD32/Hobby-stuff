#!/usr/bin/env python3

import calendar
import datetime
import os
import pickle
import time

import pyowm
import schedule
import telebot
from requests import exceptions
from tinydb import TinyDB, Query

weekdays = {'понедельник': 'Monday', 'вторник': 'Tuesday', 'среду': 'Wednesday', 'четверг': 'Thursday',
            'пятницу': 'Friday', 'субботу': 'Saturday'}

now = datetime.datetime.now()
owm = pyowm.OWM('e8eb26da01b8f30c029efefbf897846d')
justbot = telebot.TeleBot('340325873:AAGSVf33Gz59sbcqlj8BIkBgmTg3424V8yE')

que = Query()
db = TinyDB('data.db')

def get_sched(day, table):
    sched = ''
    st = "Расписание:\n"
    for item in table.search((que.weekday == day) & ((que.week=="Both") | (que.week == (int(now.strftime("%W")))% 2))):
        sched += str(item['num']) + '. ' + item['time'] + ' ' + item['name'] + \
               ', ' + str(item['hall']) + ', ' + item['lecturer'] + '\n'
    if (sched==''): st = None
    else: st += sched
    return st

def save():
    with open('justpickle', mode='wb') as out:
        pickle.dump([users], out, protocol=pickle.HIGHEST_PROTOCOL)

@justbot.message_handler(commands=['start'])
def send_welcome(message):
    justbot.send_message(message.chat.id, 'Greetings. Please, choose your group via "/set_group".\n')
    if not (message.from_user.id in users.keys()):
        users.update({message.from_user.id:None})
    save()

@justbot.message_handler(commands=['set_group'])
def set_default_group(message):
    if len(message.text.split(' ')) == 2 and message.text.split(' ')[1] in db.tables():
        users.update({message.from_user.id:message.text.split(' ')[1]})
        save()
        justbot.send_message(message.chat.id, 'Changed successfully')
    else:
        justbot.send_message(message.chat.id, 'Group not found')

@justbot.message_handler(commands=['list_groups'])
def list_groups(message):
    s = ''
    for table in db.tables():
        s += table + '\n'
    justbot.send_message(message.chat.id, s)

@justbot.message_handler(content_types=['text']) #func=lambda message: "расписание" in message.text.lower())
def show_schedule(message):
    if 'расписание' in message.text.lower():
        for word in message.text.split(' '):
            if word in weekdays.keys():
                text = get_sched(weekdays.get(word), db.table(users[message.from_user.id]))
                if text == None: text = 'В ' + word + ' нет пар'
                justbot.send_message(message.chat.id, text)
                break
            elif word == "завтра":
                text = get_sched(calendar.day_name[int(now.strftime('%w'))], db.table(users[message.from_user.id]))
                if text == None: text = 'Йеееей! Завтра нет пар!'
                justbot.send_message(message.chat.id, text)
                break
            elif word == "сегодня":
                text = get_sched(now.strftime("%A"), db.table(users[message.from_user.id]))
                if text == None: text = 'Сегодня нет пар!'
                justbot.send_message(message.chat.id, text)
                break
    elif 'расписание на расписание' in message.text.lower():
        justbot.send_message(message.chat.id, 'Совсем с цма сошёл?')
    elif 'погода' in message.text.lower():
        forecast = owm.weather_at_place('Moscow,ru').get_weather().get_temperature(unit='celsius')
        weather = 'Температура воздуха - ' + str(forecast)[8:13] + ' градусов Цельсия\n'
        justbot.send_message(message.chat.id, weather)

def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if os.path.exists("./justpickle"):
    with open("./justpickle", mode = "rb") as data:
        users = pickle.load(data)[0]
else: users = {}

#schedule.every().day.at('07:00').do(justbot.send_message("208109844", 'Приветствую! Сегодня ' + now.strftime('%x') + '\n' + 'Температура воздуха - ' + str(owm.weather_at_place('Moscow,ru').get_weather().get_temperature(unit='celsius'))[8:14] + ' градусов Цельсия\nРасписание на сегодня:\n' + get_sched(now.strftime("%A"), db.table('trash')), db.table('trash)')))

while True:
    try:
        justbot.polling(none_stop=True)
    except exceptions.ReadTimeout or exceptions.ConnectTimeout:
        time.sleep(20)

