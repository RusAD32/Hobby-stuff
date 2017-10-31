#!/usr/bin/env python3

import telebot  # Should be installed via pip
import time
import threading
import random
import schedule  # Should be installed via pip
import os
from requests import get, exceptions
from json import loads
import pickle

"""
createpoll - создать новый опрос в текущем чате
end - закончить добавление вариантов ответа в опрос
closepoll - завершить текущий опрос
results_ind - список проголосовавших и их ответы
results_stat - диаграмма соотношения голосов
roll - XdY. Эмулирует бросок X Y-гранных кубиков
roll_d6 - эмулирует бросок шестигранника
roll_d20 - эмулирует бросок двадцатигранника
roll_d100 - эмулирует бросок стогранника
reminder_on - включить уведомление о мероприятии
vk_notifier_on - group - включить уведомление о новых постах в группе"""

if os.path.exists("RPbot_token"):
    with open("RPbot_token") as token:
        TOKEN = token.read().strip()
else:
    print("Token not found! (Dayana)")
    while True:
        time.sleep(100)
if os.path.exists("RPbot_VK_token"):
    with open("RPbot_VK_token") as token:
        VK_TOKEN = token.read().strip()
else:
    print("VKToken not found! (Dayana)")
    while True:
        time.sleep(100)
bot = telebot.TeleBot(TOKEN)
greets = ("Здравствуй путник, добро пожаловать к костру!",
          "Добрый день. Общаясь со мной, помните - Искусственный интеллект не имеет шансов в столкновении с естественной глупостью.",
          "Добро пожаловать. Скоро здесь останутся лишь две группы работников: те, кто контролирует компьютеры, и те, кого контролируют компьютеры. Постарайтесь попасть в первую.",
          "Здравствуйте! Если вдруг вы услышите тихий щелчок, под ногой, знайте - это противопехотная мина. Приятного дня.",
          "Добрый день. Мы рады приветствовать вас в этом чате. Если вас кто-нибудь обидел, то это ваши проблемы.")


class Poller:
    vars = dict()
    host = 0
    question = ""
    is_ready = False
    is_closed = False
    voted = dict()

    def __init__(self, host_id):
        self.vars = {}
        self.host = host_id
        self.voted = {}

    def __call__(self, var, voter_id):
        if id in self.voted.keys():
            self.vars[self.voted[voter_id]] -= 1
        self.vars[var] += 1
        self.voted[voter_id] = var


pollers = {}
groups = {}
chats_to_notify = {}
chats_to_remind = []


def reminder(mes):
    for chat_id in chats_to_remind:
        bot.send_message(chat_id, mes)


def get_latest_post(group_name):
    with open("log", mode='a') as l:
        posts = loads(get(f"https://api.vk.com/method/wall.get?access_token={VK_TOKEN}&domain={group_name}&count=2").content)
        l.write(str(posts) + " " + str(dir(posts)))
        posts = posts['response']
    return posts[1] if posts[1]['date'] > posts[2]['date'] else posts[2]


def vk_notifier():
    temp_groups = {}
    for chat_id in chats_to_notify.keys():
        if len(chats_to_notify[chat_id]) == 0:
            chats_to_notify.pop(chat_id)
            with open("latest", mode='wb') as latest:
                pickle.dump([groups, chats_to_notify], latest)
            return
        for group in chats_to_notify[chat_id]:
            try:
                gr = loads(get(f"https://api.vk.com/method/groups.getById?access_token={VK_TOKEN}&group_id={group}").content)['response'][0]
                if gr['is_closed'] or 'deactivated' in gr.keys():
#                    chats_to_notify[chat_id].remove(group)
                    continue
            except:
                pass
            if group in temp_groups.keys():
                post = temp_groups[group]
                bot.send_message(chat_id, f"Новый пост в группе!\n\nhttps://vk.com/wall{post['to_id']}_{post['id']}")
                continue
            time.sleep(0.5)
            post = get_latest_post(group)
            if post['date'] > groups[group]:
                temp_groups[group] = post
                groups[group] = post['date']
                with open("latest", mode='wb') as latest:
                    pickle.dump([groups, chats_to_notify], latest)
                bot.send_message(chat_id, f"Новый пост в группе!\n\nhttps://vk.com/wall{post['to_id']}_{post['id']}")
            time.sleep(0.5)


def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def results(m):
    if m.chat.id in pollers.keys() and pollers[m.chat.id].is_ready:
        if len(pollers[m.chat.id].vars) == 0:
            pollers.pop(m.chat.id)
            return "Никто не проголосовал, так что я удалил этот опрос"
        ans = ''
        votes = sum(pollers[m.chat.id].vars.values())
        for key in pollers[m.chat.id].vars.keys():
            weight = 12 * pollers[m.chat.id].vars[key] // votes
            percent = round(pollers[m.chat.id].vars[key] / votes * 100)
            bar1 = '\u25ae' * weight
            bar2 = '\u25af' * (12 - weight)
            ans += f"{key}\n[{bar1}{bar2}] : {pollers[m.chat.id].vars[key]} ({percent}%)\n"
        return ans
    else:
        return ""


def close_poll(m):
    ans = results(m)
    if ans:
        pollers[m.chat.id].is_closed = True
        bot.send_message(m.chat.id, ans)


def is_adm(m):
    if m.from_user.id == m.chat.id:
        return True
    for ch_user in bot.get_chat_administrators(m.chat.id):
        if ch_user.user.id == m.from_user.id:
            return True
    return False


if os.path.exists("remind_chats"):
    with open("remind_chats", mode='rb') as rem:
        chats_to_remind = pickle.load(rem)
schedule.every().saturday.at("15:00").do(reminder,
                                         "Хочу напомнить Вам, что игра состоится в это воскресение! Большая просьба не опаздывать или предупреждать об этом заранее. Время начала мероприятия 18-00 по Москве. Место - Антикафе WoodenDoor. Милютинский переулок 6 строение 1.")
schedule.every().sunday.at("11:00").do(reminder,
                                       "Всем доброго дня. Напоминаю, что игра состоится сегодня, в 6 вечера. Подробности уточняйте у мастера, в сообщениях группы: https://vk.com/explosive_games")
if os.path.exists("latest"):
    with open("latest", mode='rb') as latest:
        lat = pickle.load(latest)
        groups = lat[0]
        chats_to_notify = lat[1]
schedule.every().minute.do(vk_notifier)
if os.path.exists("state"):
    with open("state", mode='rb') as state:
        pollers = pickle.load(state)
#schedule.every(6).hours.do(exit)
vk_notifier()


@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Добро пожаловать!")

'''
@bot.message_handler(commands=['dice'])
def bot_roll(m):
    try:
        text = m.text.lower().split(' ')[1]
    except IndexError:
        bot.send_message(m.chat.id, "Использование: /dice XdY или /dice XдY, где X, Y - некоторые числа")
        return
    div_pos = text.find('d') if 'd' in text else text.find('д')
    if div_pos == -1:
        bot.send_message(m.chat.id, "Использование: /dice XdY или /dice XдY, где X, Y - некоторые числа")
        return
    num = int(text[:div_pos])
    sides = int(text[div_pos+1:])
    mes = ""
    try:
        for i in range(num):
            mes += str(random.randint(1, sides)) + " "
    except TypeError:
        bot.send_message(m.chat.id, "Использование: /dice XdY или /dice XдY, где X, Y - некоторые числа")
        return
    bot.send_message(m.chat.id, mes)
'''

@bot.message_handler(commands=['dice_d6'])
def bot_roll_d6(m):
    bot.send_message(m.chat.id, str(random.randint(1, 6)))


@bot.message_handler(commands=['dice_d20'])
def bot_roll_d6(m):
    bot.send_message(m.chat.id, str(random.randint(1, 20)))


@bot.message_handler(commands=['dice_d100'])
def bot_roll_d6(m):
    bot.send_message(m.chat.id, str(random.randint(1, 100)))


@bot.message_handler(commands=['reminder_on'])
def bot_reminder_on(m):
    if is_adm(m):
        if m.chat.id in chats_to_remind:
            bot.send_message(m.chat.id, "Напоминания уже включены!")
            return
        chats_to_remind.append(m.chat.id)
        with open("remind_chats", mode='wb') as f:
            pickle.dump(chats_to_remind, f, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(m.chat.id, "Поставила в очередь")


@bot.message_handler(commands=['reminder_off'])
def bot_reminder_off(m):
    if is_adm(m):
        if m.chat.id not in chats_to_remind:
            bot.send_message(m.chat.id, "В этот чат напоминания и так не приходят!")
            return
        chats_to_remind.remove(m.chat.id)
        with open("remind_chats", mode='wb') as f:
            pickle.dump(chats_to_remind, f, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(m.chat.id, "Отключил")

@bot.message_handler(commands=['vk_notifier_on'])
def vk_add_reminder(m):
    if is_adm(m):
        arr = m.text.split(' ')
        try:
            date = get_latest_post(arr[1])['date']
        except:
            bot.send_message(m.chat.id, "Использование: /vk_notifier_on singing_soul_music" +
                                        "(для сообщества https://vk.com/singing_soul_music)")
            return
        groups[arr[1]] = date
        if m.chat.id not in chats_to_notify.keys():
            chats_to_notify[m.chat.id] = [arr[1]]
        else:
            chats_to_notify[m.chat.id].append(arr[1])
            chats_to_notify[m.chat.id] = list(set(chats_to_notify[m.chat.id])) #TODO убрать костыль
        with open("latest", mode='wb') as latest:
            pickle.dump([groups, chats_to_notify], latest)
        bot.send_message(m.chat.id, "Буду уведомлять")
    else:
        bot.send_message(m.chat.id, "Простите, но вы не администратор этой группы")

@bot.message_handler(commands=["vk_notifier_off"])
def vk_notifier_off(m):
    arr = m.text.split(' ')
    if m.chat.id in chats_to_notify.keys() and len(arr) > 1 and arr[1] in chats_to_notify[m.chat.id]\
            and (m.from_user.id in bot.get_chat_administrators(m.chat.id)
                 or m.from_user.id == m.chat.id):
        chats_to_notify[m.chat.id].pop(arr[1])
        still_used = False
        for gr_list in chats_to_notify.values():
            for gr in gr_list:
                if gr == arr[1]:
                    still_used = True
                    break
        if not still_used:
            groups.pop(arr[1])
        with open("latest", mode='wb') as latest:
            pickle.dump([groups, chats_to_notify], latest)
    elif m.chat.id in chats_to_notify.keys() and is_adm(m):
        for gr_to_del in chats_to_notify[m.chat.id]:
            still_used = False
            for gr_list in chats_to_notify.values():
                for gr in gr_list:
                    if gr_to_del == gr:
                        still_used = True
                        break
            if not still_used:
                groups.pop(gr_to_del)
        chats_to_notify.pop(m.chat.id)
        with open("latest", mode='wb') as latest:
            pickle.dump([groups, chats_to_notify], latest)
        bot.send_message(m.chat.id, "Все подписки отменены")
    elif not is_adm(m):
        bot.send_message(m.chat.id, "Простите, вы не являетесь администратором этой группы")
    else:
        bot.send_message(m.chat.id, "Этот чат не подписан ни на какие группы")


@bot.message_handler(commands=['createpoll'])
def new_poll(m):
    if is_adm(m):
        if m.chat.id in pollers.keys() and not pollers[m.chat.id].is_closed:
            bot.reply_to(m, "Извините, в данном чате уже запущен опрос")
        else:
            pollers[m.chat.id] = Poller(m.from_user.id)
            with open("state", mode='wb') as state:
                pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
            bot.reply_to(m, "Пришлите, пожалуйста, вопрос")


@bot.message_handler(commands=['closepoll'])
def end_poll(m):
    if is_adm(m):
        if m.from_user.id == pollers[m.chat.id].host:
            ans = results(m)
            if ans != "":
                pollers[m.chat.id].is_closed = True
                with open("state", mode='wb') as state:
                    pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
                bot.send_message(m.chat.id, ans, reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(commands=['end'])
def poll_ready(m):
    if is_adm(m):
        if (m.chat.id in pollers.keys() and m.from_user.id == pollers[m.chat.id].host and
                len(pollers[m.chat.id].vars.keys())) > 1:
            poller = pollers[m.chat.id]
            poller.is_ready = True
            markup = telebot.types.ReplyKeyboardMarkup(row_width=len(poller.vars.keys()))
            text = poller.question + '\n\n'
            for key in poller.vars.keys():
                markup.row(telebot.types.KeyboardButton(key))
                text += key + '\n'
            bot.send_message(m.chat.id, text, reply_markup=markup)
            with open("state", mode='wb') as state:
                pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
        elif m.chat.id in pollers.keys() and m.chat.id == pollers[m.m.chat.id]:
            bot.send_message(m.chat.id, "Нужно как минимум два ответа, а то какой же это опрос?")


@bot.message_handler(commands=['results_stat'])
def result_stats(m):
    if is_adm(m):
        ans = results(m)
        if ans != "":
            bot.send_message(m.chat.id, ans)


@bot.message_handler(commands=['results_ind'])
def results_ind(m):
    if is_adm(m):
        if m.chat.id in pollers.keys() and pollers[m.chat.id].is_ready:
            ans = ""
            for x in pollers[m.chat.id].voted.keys():
                ans += x + ': ' + str(pollers[m.chat.id].voted[x]) + '\n'
            bot.send_message(m.chat.id, ans)

@bot.message_handler(commands=['set_poll_autoclose'])
def set_autoclose(m):
    if is_adm(m):
        schedule.every().sunday.at("12:00").do(close_poll, m)
        bot.send_message(m.chat.id, "Сделаю")


@bot.message_handler(commands=['link'])
def send_link(m):
    bot.send_message(m.chat.id, "https://vk.com/go_to_srpg")


@bot.message_handler(commands=['reboot'])
def reboot(m):
    if is_adm(m):
        bot.send_message(m.chat.id, "OK")
        exit()


@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and pollers[m.chat.id].question == ""
                                    and m.from_user.id == pollers[m.chat.id].host)
def add_question(m):
    pollers[m.chat.id].question = m.text
    with open("state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    bot.reply_to(m, "Теперь пришлите, пожалуйста, варианты опроса, напишите /end когда закончите")


@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and not pollers[m.chat.id].is_ready
                                    and m.from_user.id == pollers[m.chat.id].host)
def new_var(m):
    pollers[m.chat.id].vars[m.text] = 0
    with open("state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    bot.reply_to(m, "Отлично, теперь отправьте мне еще один вариант или /end")


@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and pollers[m.chat.id].is_ready
                                    and not pollers[m.chat.id].is_closed
                                    and m.text in pollers[m.chat.id].vars.keys())
def answer(m):
    poller = pollers[m.chat.id]
    poller(m.text, m.from_user.first_name)
    with open("state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    bot.reply_to(m, "Отлично, ваш голос учтен")


@bot.message_handler(content_types=['new_chat_member'])
def bot_new_member_greetings(m):
    bot.send_message(m.chat.id, random.choice(greets))
    bot.send_message(m.chat.id, "Меня зовут Даяна и я помогаю вам тут ориентироваться. Для начала работы нажмите \"слэш\" и выберете команду Help.")


@bot.message_handler(commands=["help"])
def bot_cmnd(m):
    bot.send_message(m.chat.id, "Использование команд: \n" +
                     "/dice_d6 -- кинуть шестигранник\n/dice_d20 -- кинуть 20-гранник\n" +
                     "/dice_d100 -- кинуть стогранник\n/help -- вывести текущее сообщение\n\n" +
                     "Правила: https://vk.com/topic-138618758_35190639")


if __name__ == "__main__":
    t = threading.Thread(target=scheduler)
    t.daemon = True
    t.start()

    while True:
        bot.polling(none_stop=True)


