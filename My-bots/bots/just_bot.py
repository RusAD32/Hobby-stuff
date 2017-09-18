#!/usr/bin/env python3

import calendar
import datetime
import os
import pickle
import time
import pyowm
import schedule
import telebot
import sys
from requests import exceptions
from tinydb import TinyDB, Query

weekdays = {'понедельник': 'Monday', 'вторник': 'Tuesday', 'среду': 'Wednesday', 'четверг': 'Thursday',
            'пятницу': 'Friday', 'субботу': 'Saturday'}

now = datetime.datetime.now()
if os.path.exists("just_bot_owm_token"):
    with open("just_bot_owm_token") as ot:
        owm = pyowm.OWM(ot.read().strip())
else:
    sys.stderr.write("No owm token found, exiting...\n")
    sys.exit(1)
if os.path.exists("just_bot_token"):
    with open("just_bot_token") as t:
        justbot = telebot.TeleBot(t.read().strip())
else:
    sys.stderr.write("No Telegram token found, exiting...")
    sys.exit(2)

que = Query()
db = TinyDB('./bots/data.db')

def get_sched(day, table):
    sched = ''
    st = "Расписание:\n"
    for item in table.search((que.weekday == day) & ((que.week=="Both") | (que.week == (int(now.strftime("%W")))% 2))):
        sched += str(item['num']) + '. ' + item['time'] + ' ' + item['name'] + \
               ', ' + str(item['hall']) + ', ' + item['lecturer'] + '\n'
    if (sched==''): st="В день нет пар"
    else: st += sched
    return st

def save():
    with open('./bots/justpickle', mode='wb') as out:
        pickle.dump([users], out, protocol=pickle.HIGHEST_PROTOCOL)

@justbot.message_handler(commands=['start'])
def send_welcome(message):
    justbot.send_message(message.chat.id, 'Greetings. Please, choose your group via "/set_group".\n')
    if not (message.from_user.id in users.keys()):
        users.update({message.from_user.id:None})
    save()

@justbot.message_handler(commands=['set_group'])
def set_default_group(message):
    if message.text.split(' ')[1] in db.tables():
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
                justbot.send_message(message.chat.id, get_sched(weekdays.get(word), db.table(users[message.from_user.id])))
                break
            elif word == "завтра":
                justbot.send_message(message.chat.id, get_sched(calendar.day_name[int(now.strftime('%w'))], db.table(users[message.from_user.id])))
                break
            elif word == "сегодня":
                justbot.send_message(message.chat.id, get_sched(now.strftime("%A"), db.table(users[message.from_user.id])))
    elif 'погода' in message.text.lower():
        forecast = owm.weather_at_place('Moscow,ru').get_weather().get_temperature(unit='celsius')
        weather = 'Температура воздуха - ' + str(forecast)[8:13] + ' градусов Цельсия\n'
        justbot.send_message(message.chat.id, weather)

def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def morning():
    schedule.every().day.at('07:00').do(justbot.send_message("208109844", 'Приветствую! Сегодня ' + now.strftime('%x') + '\n' + 'Температура воздуха - ' + str(owm.weather_at_place('Moscow,ru').get_weather().get_temperature(unit='celsius'))[8:14] + ' градусов Цельсия\nРасписание на сегодня:\n' + get_sched(now.strftime("%A"), db.table('trash)'))))

if os.path.exists("./bots/justpickle"):
    with open("./bots/justpickle", mode = "rb") as data:
        users = pickle.load(data)[0]
else: users = {}

while True:
    try:
        justbot.polling(none_stop=True)
    except exceptions.ReadTimeout or exceptions.ConnectTimeout:
        time.sleep(20)

