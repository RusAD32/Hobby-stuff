#!/usr/bin/env python3

import config
import supermind
import ideacloud
from reminder_pb2 import reminder
import telebot
import random
import time
import threading
import sys
import requests
import os
import socket
import schedule
import pickle


if os.path.exists("rusad_bot_token"):
    with open("rusad_bot_token") as token:
        TOKEN = token.read().strip()
    print(TOKEN)
else:
    print("Token not found! (RusAD) ")
    while(True):
        time.sleep(100)
rusad = telebot.TeleBot(TOKEN)
if os.path.exists("./rusad_state"):
    with open("./rusad_state", mode = "rb") as state:
        games, usrs, wgs, active_wgs, ideaers, animeers = pickle.load(state)
else:
    games = {}
    db = open("./db", mode='r')     #TODO: переделать в нормальную базу данных
    strs = db.read().split('\n')
    db.close()
    usrs = {}
    wgs = {}
    active_wgs = {}
    ideaers = {}
    animeers = []
    if os.path.exists("./wgs"):
        wgs = ideacloud.load("./wgs")
    for x in strs:
      if (x.strip() != ''):
          y = x.split(' ')
          usrs[y[0]] = int(y[1])
          if len(y) == 3 and y[2] == 'nya':
              animeers.append(int(y[1]))
          elif len(y) >= 3:
              active_wgs[int(y[1])] = wgs[y[2]]
              if len(y) == 4:
                  animeers.append(int(y[1]))
    if os.path.exists("./sm"):
        games = supermind.load()

    if not os.path.exists("./ideas"): # Он же на моем личном компе, так что папка там определенно есть. Почему я еще не удалил эти строки?
        os.mkdir("./ideas")
    with open("rusad_state", mode='wb') as state:
        pickle.dump([games, usrs, wgs, active_wgs, ideaers, animeers], state, protocol = pickle.HIGHEST_PROTOCOL)
mood_replies_ru = {"normal":config.replies_ru_norm,
                   "good":config.replies_ru_good,
                   "bad":config.replies_ru_bad,
                   "tsun":config.replies_ru_tsun,
                   "dere":config.replies_ru_dere,
                   "genki":config.replies_ru_genki,
                   "deredere":config.replies_ru_deredere}
                   

if os.path.exists("./rusad_bot_errlog"):
    with open("./rusad_bot_errlog") as errs:
        errtext = errs.read()
        if errtext.split('\n')[0] == 'disconnected':
            pass
        else:
            with open("./blame") as f:
                name = int(f.read().strip())
            rusad.send_message(name, errtext)
    os.remove("./rusad_bot_errlog")
else:
    rusad.send_message(usrs['polocky'], "Я перезагрузился. Скорее всего, меня обновили")
                   

class mooder:
    mood = "normal"
    moods = []

    def __init__(self, moods):
        self.moods = moods
        self.mood = random.choice(self.moods)

    def __call__(self):
        self.mood = random.choice(self.moods)
        time.sleep(random.randint(900, 3*3600))

mdr = mooder(['good', 'normal', 'bad'])
mdr_anim = mooder(list(mood_replies_ru.keys()) + ['tsundere'])

def change_moods(mooder):
    while True:
        mooder()

def send_alerts():
    if os.path.exists("./sender"):
        os.remove("./sender")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind("./sender")
    server.listen(3)
    while True:
        conn, addr = server.accept()
        data = reminder()
        data.ParseFromString(conn.recv(8192))
        rusad.send_message(data.uid, data.mes)
        conn.close()
 
def alerter(usr, waittime, msg):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect("./alerts")
    rem = reminder()
    rem.uid = usr
    rem.ttw = waittime
    rem.mes = msg
    client.send(rem.SerializeToString())
    client.close()

def save():
    with open("rusad_state", mode='wb') as state:
        pickle.dump([games, usrs, wgs, active_wgs, ideaers, animeers], state, protocol = pickle.HIGHEST_PROTOCOL)

def get_replies(message):
    cur_mood = mdr_anim.mood if message.from_user.id in animeers else mdr.mood
    return random.choice((mood_replies_ru['tsun'], mood_replies_ru['dere'])) if cur_mood == 'tsundere' else mood_replies_ru[cur_mood]

def bot_random(arr): 
    if len(arr) > 0 and arr[0] == 'метро':
        line_no = random.randint(0,len(config.metro)-1)
        line = config.metro[line_no]
        msg = str(line_no+1) + ' ветка, ' + config.lines[line_no] + ', станция ' + random.choice(line)
    elif len(arr) > 0:
        fstel = arr[0][:-1] if arr[0][-1] == ',' else arr[0]
        first = int(fstel) if fstel.isdigit() else 0
        sndel = arr[1] if len(arr) > 1 else '0'
        second = int(sndel) if sndel.isdigit() else 0
        msg = str(random.randint(min(first, second), max(first, second)))
    return msg

def bot_choice(arr, replies):
    i = 0
    choice1 = ''
    while not 'или' == arr[i].lower():
        choice1 += arr[i] + ' '
        i += 1
    choice2 = ''
    for x in arr[i+1:]:
        choice2 += x + ' '
    if choice2[-2] == '?':
        choice2 = choice2[:-2]
    msg = replies.my_choice_is + random.choice((choice1, choice2))
    return msg

def bot_remind(arr, message, replies):
    if 1:#try:
        msg_to_rem = ''
        i = 0
        for i in range (0, len(arr)):
            if arr[i][0] == "@":
                name = arr[i][1:].lower()
                if arr[i+1] == 'в' and arr [i+2] == 'чат':
                    usr_to_rem = message.chat.id
                    msg_to_rem = '@' + name + ' '
                    i += 2
                    break
                elif name in usrs.keys():
                    msg_to_rem = 'От @' + message.from_user.username + ': '
                    usr_to_rem = usrs[name]
                    break
                else:
                    return replies.no_such_user
            elif 'мне' in arr[i]:
                if arr[i+1] == 'в' and arr [i+2] == 'чат':
                    usr_to_rem = message.chat.id
                    msg_to_rem = '@' + message.from_user.username + ' '
                    i += 2
                    break
                else:
                    usr_to_rem = message.from_user.id
                    break
        i+=1
        if arr[i] == 'через':
            time_to_wait = 0
            timearr = []
            for x in arr[i+1:]:
                if (x[0] != '"' and x[0] != "'" and x != 'что'):
                    timearr.append(x)
                else:
                    break
            i += len(timearr) + 1
            for j in range (0, len(timearr), 2):
                if timearr[j+1][:3] == 'час':
                    time_to_wait += int(timearr[j])*3600
                elif timearr[j+1][:3] == 'мин':
                    time_to_wait += int(timearr[j])*60
                elif timearr[j+1][:3] == 'сек':
                    time_to_wait += int(timearr[j])
        elif arr[i] == 'в':
            time_to_rem = arr[i+1].split(':')
            if len(time_to_rem[-1]) == 3:
                time_to_rem[-1] = time_to_rem[-1][:-1]
            while len(time_to_rem) < 3:
                time_to_rem += ['00']
            i+=2
            cur_time = str(time.ctime()).split(' ')[3].split(':')
            time_to_wait = (int(time_to_rem[0]) - int(cur_time[0]))*3600 + (int(time_to_rem[1]) - int(cur_time[1]))*60 + int(time_to_rem[2]) - int(cur_time[2])
            if time_to_wait < 0:
                time_to_wait += 24*3600
        sep = arr[i][0]
        if sep == 'ч':
            i+=1
        else:
            arr[i] = arr[i][1:]
            arr[-1] = arr[-1][:-1]
        for x in arr[i:]:
            msg_to_rem += x + ' '
        alerter(usr_to_rem, time_to_wait, msg_to_rem)
        msg = replies.correct_alert
    else:#except:
        msg = replies.wrong_alert
    return msg

def bot_save_quote(message, replies):
    if (message != None and message.text != None):
        quote_book = open("./quotes/" + str(message.chat.id), mode = 'a')
        quote_book.write(message.text + ' © ' + message.from_user.username + '\n\n')
        quote_book.close()
        msg = replies.quoted
    else:
        msg = replies.nothing_to_quote
    return msg

def bot_give_saved(name, dpath, replies):
    if os.path.exists(dpath + name):
        with open(dpath + name, mode = 'r') as book:
            items = book.read().split('\n\n')[:-1]
            if len(items) != 0:
                msg = random.choice(items)
            else:
                msg = replies.no_quotes
    else:
        msg = replies.no_quotes
    return msg

def bot_adm_send_source(message, replies):
    if message.from_user.id in config.developers and message.from_user.id == message.chat.id:
        with open("./rusad_bot.py", mode = 'r') as source:
            rusad.send_document(message.chat.id, source)
        with open("./config.py", mode = 'r') as conf:
            rusad.send_document(message.chat.id, conf)
        msg = 'Вот'
    else:
        msg = replies.wrong_command
    return msg

def check_valid(number):
    if not number.isdigit():
        return 1
    elif len(number) != 4:
        return 2
    for i in range (0, len(number) - 1):
        if number[i] in number[i+1:]:
            return 3
    return 0

def bot_delete_saved(pids, dpaths, num, text_to_delete, replies):
    ok = False
    where = ''
    needed_list = []
    for pid in pids:
        for dpath in dpaths:
            try:
                with open(dpath + pid) as file:
                    lst = file.read().split('\n\n')
                    if num != -1:
                        try:
                            lst.pop(num)
                        except IndexError:
                            return "Ты столько не сохранял" # добавить настроения
                        needed_list = lst
                        where = dpath + pid
                        ok = True
                    elif text_to_delete in lst:
                        lst.remove(text_to_delete)
                        needed_list = lst
                        where = dpath + pid
                        ok = True
            except FileNotFoundError:
                pass
    if ok:
        with open(where, mode = 'w') as file:
            for x in needed_list[:-1]:
                file.write(x + '\n\n')
        return replies.delete_ok
    else:
        return replies.delete_fail

def bot_give_all_ideas(src, replies):
    if not os.path.exists("./ideas/" + src):
        return [replies.no_ideas]
    with open("./ideas/" + src) as ideas:
        all_ideas = ideas.read()
        if len(all_ideas) > 0:
            return telebot.util.split_string(all_ideas, 3000)
        else:
            return [replies.no_ideas]

def bot_supermind(message, replies):
    code = check_valid(message.text)
    if code == 1 and "история" == message.text.lower():
        msg = games[message.from_user.id].guesses_table()
    elif code == 1 and "стоп" == message.text.lower():
        msg = replies.sm_stop_msg
        games.pop(message.from_user.id)
        save()
    elif code == 1:
        msg = ''
    elif code == 2:
        msg = replies.sm_bad_quantity
    elif code == 3:
        msg = replies.sm_repeated_digit
    else:
        msg = games[message.from_user.id](message.text)
    save()
    return msg

def bot_roll_dice(arr, replies, chid):
    n, m = 1, 6
    try:
        if arr[0].isdigit():
            n = int(arr[0])
            if arr[1][1:].isdigit():
                m = int(arr[1][1:])
            elif arr[1] == 'd' or arr[1] == 'д':
                m = int(arr[2])
        else:
            nm = arr[0].split('d')
            if len(nm) == 1:
                nm = nm[0].split('д')
            n = int(nm[0])
            m = int(nm[1])
    except:
        pass
    msg = ''
    for i in range (0, n):
        msg += str(random.randint(1, m)) + ' '
        if len(msg) > 2900:
            rusad.send_message(chid, msg)
            msg = ""
    return msg

def parse_msg(message):
    replies = get_replies(message)
    arr = message.text.lower().split(' ')
    obr = False
    if 'ярик' in arr[0] or 'rusad' in arr[0]:
        obr = True
        arr = arr[1:]    
    if len(arr) < 1:
        msg = random.choice(("Я!", "Чего?"))
    for i in range (0, len(arr)):
        if message.from_user.id in ideaers.keys():
            if len(arr) == 1 and 'все' in arr[i] or 'всё' in arr[i]:
                ideaers.pop(message.from_user.id)
                msg = replies.ok
            else:
                with open("./ideas/" + ideaers[message.from_user.id], mode = 'a') as ideabook:
                    ideabook.write(message.text + '\n\n')
                msg = replies.quoted
            break
        elif ('нарандомь' in arr[i] and len(arr) > i + 1): # а надо ли?
            msg = bot_random(arr[i+1:])
            break
        elif 'привет' in arr[i]:
            msg = 'И тебе привет, ' + message.from_user.first_name + '!'
            break
        elif 'спасибо' in arr[i]:
            msg = random.choice(('Пожалуйста, ' + message.from_user.first_name + '!', 'Не за что, ' + message.from_user.first_name + '!'))
            break
        elif len(arr) > i + 1 and "ты" in arr[i] and "жив" in arr[i+1]:
            msg = "Да!"
            break
        elif (len(arr) > i + 2 and ('расскажи' in arr[i] and 'о' in arr[i+1] and 'себ' in arr[i+2])
              or ('что' in arr[i] and 'ты' in arr[i+1] and ('умеешь' in arr[i+2] or 'можешь' in arr[i+2]))):
            msg = config.help_msg
            break
        elif 'идея' in arr[i]:
            if len(arr) > i + 2 and "групп" in arr[i+2]:
                if len(arr) > i + 3:
                    dest = wgs[arr[i+3]].name
                elif message.from_user.id in active_wgs.keys():
                    dest = active_wgs[message.from_user.id].name
            else:
                dest = str(message.from_user.id)
            ideaers[message.from_user.id] = dest
            msg = replies.listening
            break
        elif len(arr) > i+1 and "помоги" in arr[i] and "решить" in arr[i+1]:
            arr2 = message.text.split(' ')
            if obr:
                arr2 = arr2[1:]
            msg = bot_choice(arr2[i+2:], replies)
            break
        elif 'напомни' in arr[i]:
            msg = bot_remind(arr[i+1:], message, replies)
            break
        elif len(arr) > i + 1 and 'в' in arr[i] and 'цитатник' in arr[i+1]:
            msg = bot_save_quote(message.reply_to_message, replies)
            break
        elif 'цитату' in arr[i]:
            msg = bot_give_saved(str(message.chat.id), "./quotes/", replies)
            break
        elif 'идею' in arr[i]:
            if message.from_user.id in active_wgs.keys():
                src = active_wgs[message.from_user.id].name
            else:
                src = str(message.from_user.id)
            msg = bot_give_saved(src, "./ideas/", replies)
            break
        elif 'идеи' in arr[i]:
            if message.from_user.id in active_wgs.keys():
                src = active_wgs[message.from_user.id].name
            else:
                src = str(message.from_user.id)
            msgs = bot_give_all_ideas(src, replies)
            for msg in msgs[:-1]:
                rusad.send_message(message.chat.id, msg)
            msg = msgs[-1]
            break
        elif len(arr) > i + 1 and "мою" in arr[i] and 'идею' in arr[i+1]:
            msg = bot_give_saved(str(message.from_user.id), "./ideas/", replies)
            break
        elif len(arr) > i + 1 and "мои" in arr[i] and "идеи" in arr[i+1]:
            msgs = bot_give_all_ideas(str(message.from_user.id), replies)
            for msg in msgs[:-1]:
                rusad.send_message(message.chat.id, msg)
            msg = msgs[-1]
            break
        elif 'удали' in arr[i] and message.reply_to_message != None:
            if message.from_user.id in active_wgs.keys():
                src = (str(message.from_user.id), active_wgs[message.from_user.id].name)
            else:
                src = (str(message.from_user.id),)
            msg = bot_delete_saved(src, ("./ideas/", "./quotes/"), -1, message.reply_to_message.text, replies)
            break
        elif 'удали' in arr[i]:
            if len(arr) > i + 2 and arr[i+2].isdigit() and 'цитату' in arr[i+1]:
                msg = bot_delete_saved((str(message.chat.id),), ("./quotes/",), int(arr[i+2])-1, '', replies)
            elif len(arr) > i + 3 and arr[i+3].isdigit() and 'мою' in arr[i+1] and 'идею' in arr[i+2]:
                msg = bot_delete_saved((str(message.from_user.id),), ("./ideas/",), int(arr[i+3])-1, '', replies)
            elif len(arr) > i + 3 and arr[i+3].isdigit() and 'идею' in arr[i+1] and 'группы' in arr[i+2]:
                msg = bot_delete_saved((active_wgs[message.from_user.id].name,), ("./ideas/",), int(arr[i+3])-1, '', replies)
            else:
                msg = replies.nothing_to_del
            break
        elif len(arr) > i + 1 and "все" in arr[i] and "цитаты" in arr[i+1]:
            with open("./quotes/" + str(message.chat.id)) as quotes:
                text = quotes.read()
                if len(text) > 0:
                    msgs = telebot.util.split_string(text, 3000)
                    for msg in msgs[-1]:
                        rusad.send_message(message.chat.id, msg)
                    msg = msgs[-1]
                else:
                    msg = replies.no_quotes
            break
        elif "супермайнд" in arr[i] or "supermind" in arr[i]:
            if message.from_user.id in games.keys():
                msg = message.from_user.first_name + sm_already_playing
            else:  
                games[message.from_user.id] = supermind.game()
                supermind.save(games)
                msg = replies.sm_beginning + message.from_user.first_name + replies.sm_input
            break
        elif 'исходники' in arr[i] or len(arr) > i + 1 and 'скинь' in arr[i] and 'код' in arr[i+1]:   
            msg = bot_adm_send_source(message, replies)
            break
        elif "кинь" in arr[i] or "ролл" in arr[i] or "roll" in arr[i]:
            msg = bot_roll_dice(arr[i+1:], replies, message.chat.id)
            break
        else:
            msg = replies.wrong_command
    return msg

@rusad.message_handler(commands=['quote'])
def send_quote(message):
    rusad.send_message(message.chat.id, bot_give_quote(message.chat.id))

@rusad.message_handler(commands=['start'])
def send_welcome(message):
    if (message.from_user.username != None and not message.from_user.username.lower() in usrs.keys()):
        f = open("./db", mode='a')
        f.write(message.from_user.username.lower() + " " + str(message.from_user.id) + '\n')
        f.close()
        usrs.update({message.from_user.username.lower():message.from_user.id})
    rusad.reply_to(message, config.greetings)

@rusad.message_handler(commands=['help'])
def help(message):
    rusad.send_message(message.chat.id, config.help_msg)

@rusad.message_handler(commands=['mood'])
def send_mood(message):
    rusad.send_message(message.chat.id, mdr_anim.mood if message.from_user.id in animeers else mdr.mood)

@rusad.message_handler(commands=['supermind'])
def new_game(message):
    replies = get_replies(message)
    if message.from_user.id in games.keys():
        rusad.send_message(message.chat.id, message.from_user.first_name + ', я уже играю с тобой!')
    else:  
        games[message.from_user.id] = supermind.game()
        save()
        rusad.send_message(message.chat.id, replies.sm_beginning + message.from_user.first_name + replies.sm_input)

@rusad.message_handler(commands=['add_workgroup'])
def add_wg(message):
    replies = get_replies(message)
    arr = message.text.split(' ')
    if len(arr) == 1:
        rusad.send_message(message.chat.id, replies.addwg_usage)
    else:
        wg = ideacloud.Workspace(message.text.split(' ')[1])
        wg.add_user(message.from_user.id)
        wg.add_leader(message.from_user.id)
        wgs[wg.name] = wg
        active_wgs[message.from_user.id] = wg
        save()

@rusad.message_handler(commands=['chmood'])
def chmood(message):
    mdr_anim.mood = random.choice(mdr_anim.moods)
    
@rusad.message_handler(commands=['add_user'])
def add_usr_to_group(message):
    replies = get_replies(message)
    asker = message.from_user.id
    if asker in active_wgs[asker].leaders:
        arr = message.text.split(' ')
        if len(arr) == 1:
            rusad.send_message(message.chat.id, replies.addusr_usage)
        else:
            if arr[1][0] == '@':
                arr[1] = arr[1][1:]
            if arr[1] in usrs.keys():
                active_wgs[asker].add_user(usrs[arr[1]])
                save()
                rusad.send_message(message.chat.id, replies.wg_added)
            else:
                rusad.send_message(message.chat.id, replies.wg_nevermet)
    else:
        rusad.send_message(message.chat.id, replies.wg_notanadmin)
    
@rusad.message_handler(commands=['add_adm'])
def add_adm_to_group(message):
    replies = get_replies(message)
    asker = message.from_user.id
    if asker in active_wgs[asker].leaders:
        arr = message.text.split(' ')
        if len(arr) == 1:
            rusad.send_message(message.chat.id, replies.addadm_usage)
        else:
            if arr[1][0] == '@':
                arr[1] = arr[1][1:]
            if arr[1] in usrs.keys():
                active_wgs[asker].add_leader(usrs[arr[1]])
                save()
                rusad.send_message(message.chat.id, "Добавил")
            else:
                rusad.send_message(message.chat.id, replies.wg_nevermet)
    else:
        rusad.send_message(message.chat.id, replies.wg_notanadmin)
        
@rusad.message_handler(commands=['set_active'])
def set_active(message):
    replies = get_replies(message)
    arr = message.text.split(' ')
    if len(arr) == 1:
        rusad.send_message(message.chat.id, replies.setactive_usage)
    elif arr[1] in wgs.keys():
        if message.from_user.id in wgs[arr[1]].users:
            active_wgs[message.from_user.id] = wgs[arr[1]]
            save()
            rusad.send_message(message.chat.id, replies.wg_changed + arr[1])
        else:
            rusad.send_message(message.chat.id, replies.wg_notamember)
    else:
        rusad.send_message(message.chat.id, replies.wg_nosuchgroup)

@rusad.message_handler(commands=['delete_user'])
def delete_user(message):
    replies = get_replies(message)
    asker = message.from_user.id
    if asker in active_wgs[asker].leaders:
        arr = message.text.split(' ')
        if len(arr) == 1:
            rusad.send_message(message.chat.id, replies.deleteusr_usage)
        else:
            if arr[1][0] == '@':
                arr[1] = arr[1][1:]
            uid = usrs[arr[1]]
            if uid in active_wgs[asker].users:
                active_wgs[asker].remove_user(uid)
                if uid in active_wgs.keys() and active_wgs[uid] == active_wgs[asker]:
                    active_wgs.pop(uid)
                save()
                rusad.send_message(message.chat.id, replies.wg_deletesucc)
            else:
                rusad.send_message(message.chat.id, replies.wg_notingroup)
    else:
        rusad.send_message(message.chat.id, replies.wg_notanadmin) 

@rusad.message_handler(commands=['delete_adm'])
def delete_adm(message):
    replies = get_replies(message)
    asker = message.from_user.id
    if asker in active_wgs[asker].leaders:
        arr = message.text.split(' ')
        if len(arr) == 1:
            rusad.send_message(message.chat.id, replies.deleteadm_usage)
        else:
            if arr[1][0] == '@':
                arr[1] = arr[1][1:]
            uid = usrs[arr[1]]
            if uid in active_wgs[asker].leaders:
                active_wgs[asker].remove_leader(uid)
                save()
                rusad.send_message(message.chat.id, replies.wg_admdelsucc)
            else:
                rusad.send_message(message.chat.id, replies.wg_notinadmins)
    else:
        rusad.send_message(message.chat.id, replies.wg_notanadmin)

@rusad.message_handler(commands=['list_users'])
def list_users(message):
    replies = get_replies(message)
    msg = ''
    if message.from_user.id in active_wgs.keys():
        for x in active_wgs[message.from_user.id].users:
            try:
                msg += rusad.get_chat_member(x, x).user.first_name + ' '
            except:
                try:
                    msg += rusad.get_chat_member(message.chat.id, x).user.first_name + ' '
                except:
                    msg += str(x) + replies.wg_cantread
    else:
        msg = replies.wg_noactive
    rusad.send_message(message.chat.id, msg)                      

@rusad.message_handler(commands=['list_adms'])
def list_users(message):
    replies = get_replies(message)
    msg = ''
    if message.from_user.id in active_wgs.keys():
        for x in active_wgs[message.from_user.id].leaders:
            try:
                msg += rusad.get_chat_member(x, x).user.first_name + ' '
            except:
                try:
                    msg += rusad.get_chat_member(message.chat.id, x).user.first_name + ' '
                except:
                    msg += str(x) + replies.wg_cantread
    else:
        msg = replies.wg_noactive
    rusad.send_message(message.chat.id, msg)

@rusad.message_handler(commands=['curr_group'])
def curr_group(message):
    replies = get_replies(message)
    if message.from_user.id in active_wgs.keys():
        rusad.send_message(message.chat.id, active_wgs[message.from_user.id].name)
    else:
        rusad.send_message(message.chat.id, replies.wg_noactive)            

@rusad.message_handler(commands=["guesses"])
def show_guesses(message):
    replies = get_replies(message)
    if message.from_user.id in games.keys():
        rusad.send_message(message.chat.id, games[message.from_user.id].guesses_table())
    else:  
        rusad.send_message(message.chat.id, replies.guesses_usage)

@rusad.message_handler(commands=['roll'])
def roll_dice(message):
    rusad.send_message(message.chat.id, bot_roll_dice(message.text.lower().split(' ')[1:], mood_replies_ru[mdr.mood], message.chat.id))

@rusad.message_handler(commands=['upd'])
def update_by_cmnd(message):
    if message.from_user.id in config.developers:
        sys.stdout.write(str(message.from_user.id))
        rusad.send_message(message.chat.id, str(message.from_user.username))
        sys.exit()

@rusad.message_handler(commands=['anime_on'])
def anime_on(message):
    if not message.from_user.id in animeers:
        animeers.append(message.from_user.id)
        save()
        rusad.send_message(message.chat.id, config.anime_on)
    else:
        rusad.send_message(message.chat.id, config.anime_already_on)

@rusad.message_handler(commands=['anime_off'])
def anime_on(message):
    if message.from_user.id in animeers:
        animeers.remove(message.from_user.id)
        save()
        rusad.send_message(message.chat.id, config.anime_off)
    else:
        rusad.send_message(message.chat.id, config.anime_already_off)

    
@rusad.message_handler(content_types=["text"])
def answerer(message):
    special_msg = False
    if (message.from_user.username != None and not message.from_user.username.lower() in usrs.keys()):
        usrs.update({message.from_user.username.lower():message.from_user.id})
        with open("rusad_state", mode='wb') as state:
            pickle.dump([games, usrs, wgs, active_wgs, ideaers, animeers], state, protocol = pickle.HIGHEST_PROTOCOL)
    if message.from_user.id == usrs['catoflight'] and random.randint(1,4800) == 4800:
        special_msg = True
        rusad.send_message(message.chat.id, "Сишечка, я тебя больше не люблю") # заказной костыль
    if message.from_user.id in games.keys():
        special_msg = True
        responce = bot_supermind(message, get_replies(message))
        if "Правильно" in responce and message.from_user.id == usrs["justbucket"]:
            responce = 'Правильно! Вы подебили!' # заказной костыль
        if responce:
            rusad.reply_to(message, responce)
        else:
            special_msg = False
        if "Правильно" in responce or "К сожалению" in responce:
            games.pop(message.from_user.id)
            save()
    if not special_msg and (message.text[0:4].lower() == 'ярик' or message.text[0:5].lower() == 'rusad' or
      message.from_user.id == message.chat.id or message.from_user.id in ideaers.keys()):
        rusad.send_message(message.chat.id, parse_msg(message))
    else:
        pass

if __name__ == '__main__':
    t = threading.Thread(target = send_alerts)
    t.daemon = True
    t.start()
    moods = threading.Thread(target = change_moods, args = (mdr,))
    moods.daemon = True
    moods.start()
    moods_anim = threading.Thread(target = change_moods, args = (mdr_anim,))
    moods_anim.daemon = True
    moods_anim.start()
    while True:
        try:
            rusad.polling(none_stop=True)
        except requests.exceptions.ReadTimeout:
            time.sleep(10)
           
