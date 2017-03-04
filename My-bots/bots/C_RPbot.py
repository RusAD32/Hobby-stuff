#!/usr/bin/env python3.6

import telebot  # Should be installed via pip
import time
import threading
import schedule  # Should be installed via pip
import os
from requests import exceptions
import pickle


if os.path.exists("C_RPbot_token"):
    with open("C_RPbot_token") as token:
        TOKEN = token.read().strip()
else:
    print("Token not found!")
    while True:
        time.sleep(100)
bot = telebot.TeleBot(TOKEN)
pollers = {}
autoclose = []


class Poller:
    vars = dict()
    host = 0
    chat = 0
    question = ""
    is_ready = False
    is_closed = False
    voted = dict()

    def __init__(self, host_id, chat_id):
        self.vars = {}
        self.host = host_id
        self.chat = chat_id
        self.voted = {}

    def __call__(self, var, voter_id):
        if voter_id in self.voted.keys():
            self.vars[self.voted[voter_id]] -= 1
        self.vars[var] += 1
        self.voted[voter_id] = var


class Quiz(Poller):
    correct = ""

    def __init__(self, host_id, chat_id):
        super().__init__(host_id, chat_id)


def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def results(chat, is_closing=False):
    if chat in pollers.keys() and pollers[chat].is_ready:
        ans = pollers[chat].question + "\n\n"
        votes = sum(pollers[chat].vars.values())
        if votes != 0:
            for key in pollers[chat].vars.keys():
                weight = 12 * pollers[chat].vars[key] // votes
                percent = round(pollers[chat].vars[key] / votes * 100)
                bar1 = '\u25ae' * weight
                bar2 = '\u25af' * (12 - weight)
                ans += f"{key}\n[{bar1}{bar2}] : {pollers[chat].vars[key]} ({percent}%)"
                if "Quiz" in str(type(pollers[chat])) and (pollers[chat].is_closed or is_closing) \
                        and key == pollers[chat].correct:
                    ans += " \u2713"
                ans += "\n"
            return ans
        elif is_closing:
            bot.send_message(chat, "Никто еще не ответил. Если вы так сильно хотите закрыть этот опрос, проголосуйте сами")
            return ""
        else:
            return ""
    else:
        return ""


def close_poll(chat):
    if len(pollers[chat].vars) == 0:
        pollers.pop(chat)
        bot.send_message(chat, "Никто не проголосовал, так что я удалил этот опрос")
        return
    ans = results(chat, True)
    if ans:
        pollers[chat].is_closed = True
        with open("Cbot_state", mode='wb') as state:
            pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(chat, ans, reply_markup=telebot.types.ReplyKeyboardRemove())


def is_adm(m):
    if m.from_user.id == m.chat.id:
        return True
    for ch_user in bot.get_chat_administrators(m.chat.id):
        if ch_user.user.id == m.from_user.id:
            return True
    return False

if os.path.exists("autoclose"):
    with open("autoclose", mode='rb') as aut:
        autoclose = pickle.load(aut)
        for chat in autoclose:
            schedule.every().sunday.at("12:00").do(close_poll, chat).tag(str(chat))
if os.path.exists("Cbot_state"):
    with open("Cbot_state", mode='rb') as state:
        pollers = pickle.load(state)
schedule.every().thursday.at("12:00").do(lambda: bot.send_message(217177334, "Си, а ты не забыла про опрос?"))


@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Приветствую!\nПрежде, чем создавать опрос (/createpoll) или тест (/createquiz), " +
                                "убедитесь, что вы начали со мной беседу через личные сообщения")


@bot.message_handler(commands=['createquiz'])
def new_poll(m):
    if m.chat.id in pollers.keys() and not pollers[m.chat.id].is_closed:
        bot.reply_to(m, "Извините, в данном чате уже запущен опрос")
    else:
        quiz = Quiz(m.from_user.id, m.chat.id)
        pollers[m.from_user.id] = quiz
        pollers[m.chat.id] = Quiz(0, 0)
        with open("Cbot_state", mode='wb') as state:
            pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(m.from_user.id, "Пришлите, пожалуйста, вопрос")


@bot.message_handler(commands=['createpoll'])
def new_poll(m):
    if m.chat.id in pollers.keys() and not pollers[m.chat.id].is_closed:
        bot.reply_to(m, "Извините, в данном чате уже запущен опрос")
    else:
        poll = Poller(m.from_user.id, m.chat.id)
        pollers[m.chat.id] = Poller(0, 0)
        pollers[m.from_user.id] = poll
        with open("Cbot_state", mode='wb') as state:
            pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(m.from_user.id, "Пришлите, пожалуйста, вопрос")


@bot.message_handler(commands=['closepoll'])
def end_poll(m):
    if m.chat.id in pollers.keys() and m.from_user.id == pollers[m.chat.id].host:
        ans = results(m.chat.id, True)
        if ans != "":
            pollers[m.chat.id].is_closed = True
            with open("Cbot_state", mode='wb') as state:
                pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
            bot.send_message(m.chat.id, ans, reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(commands=['end'])
def poll_ready(m):
    if (m.chat.id in pollers.keys() and len(pollers[m.chat.id].vars.keys())) > 1 \
            and m.chat.id == pollers[m.chat.id].host:
        poller = pollers[m.chat.id]
        markup = telebot.types.ReplyKeyboardMarkup(row_width=len(poller.vars.keys()))
        text = poller.question + '\n\n'
        for key in poller.vars.keys():
            markup.row(telebot.types.KeyboardButton(key))
            text += key + '\n'
        poller.is_ready = True
        if "Quiz" in str(type(poller)):
            bot.send_message(poller.host, "Выберите правильный ответ", reply_markup=markup)
            return
        pollers.pop(m.from_user.id)
        pollers[poller.chat] = poller
        bot.send_message(m.chat.id, "Опрос создан. Чтобы завершить его, введите команду /closepoll в чате, где проводится опрос",
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(poller.chat, text, reply_markup=markup)
        with open("Cbot_state", mode='wb') as state:
            pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    elif m.chat.id in pollers.keys() and m.chat.id == pollers[m.chat.id].host:
        bot.send_message(m.chat.id, "Нужно как минимум два ответа, а то какой же это опрос?")


@bot.message_handler(commands=['results_stat'])
def result_stats(m):
    ans = results(m.chat.id)
    if ans != "":
        bot.send_message(m.chat.id, ans)


@bot.message_handler(commands=['results_ind'])
def results_ind(m):
    if m.chat.id in pollers.keys() and pollers[m.chat.id].is_ready:
        ans = pollers[m.chat.id].question + "\n\n"
        for x in pollers[m.chat.id].voted.keys():
            vote = pollers[m.chat.id].voted[x]
            ans += x + ': ' + vote
            if "Quiz" in str(pollers[m.chat.id]) and pollers[m.chat.id].is_closed \
                    and vote == pollers[m.chat.id].correct:
                ans += " \u2713"
            ans += "\n"
        bot.send_message(m.chat.id, ans)


@bot.message_handler(commands=['set_poll_autoclose'])
def set_autoclose(m):
    if m.chat.id not in autoclose:
        autoclose.append(m.chat.id)
        schedule.every().sunday.at("12:00").do(close_poll, m.chat.id).tag(str(m.chat.id))
        with open("autoclose", mode = "wb") as aut:
            pickle.dump(autoclose, aut, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(m.chat.id, "Сделаю")


@bot.message_handler(commands=['disable_poll_autoclose'])
def disable_autoclose(m):
    if is_adm(m) or m.from_user.id == 217177334:
        autoclose.remove(m.chat.id)
        schedule.clear(str(m.chat.id))
        with open("autoclose", mode = "wb") as aut:
            pickle.dump(autoclose, aut, protocol=pickle.HIGHEST_PROTOCOL)
        bot.send_message(m.chat.id, "Хорошо, опросы не будут автоматически закрываться")
    else:
        bot.send_message(m.chat.id, "Только админ может выключить эту функцию")


@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and pollers[m.chat.id].question == ""
                                    and m.from_user.id == pollers[m.chat.id].host)
def add_question(m):
    pollers[m.chat.id].question = m.text
    with open("Cbot_state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    bot.reply_to(m, "Теперь пришлите, пожалуйста, варианты ответа, напишите /end когда закончите")


@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and not pollers[m.chat.id].is_ready
                                    and m.from_user.id == pollers[m.chat.id].host)
def new_var(m):
    pollers[m.chat.id].vars[m.text] = 0
    with open("Cbot_state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    bot.reply_to(m, "Отлично, теперь отправьте мне еще один вариант или /end")


@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and "Quiz" in str(type(pollers[m.chat.id]))
                                    and m.text in pollers[m.chat.id].vars.keys()
                                    and pollers[m.chat.id].is_ready
                                    and pollers[m.chat.id].correct == "")
def correct_answer(m):
    poller = pollers[m.chat.id]
    pollers.pop(m.from_user.id)
    pollers[poller.chat] = poller
    poller.correct = m.text
    with open("Cbot_state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=len(poller.vars.keys()))
    text = poller.question + '\n\n'
    for key in poller.vars.keys():
        markup.row(telebot.types.KeyboardButton(key))
        text += key + '\n'
    bot.send_message(m.chat.id, "Опрос создан", reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.send_message(poller.chat, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.chat.id in pollers.keys()
                                    and pollers[m.chat.id].is_ready
                                    and not pollers[m.chat.id].is_closed
                                    and m.text in pollers[m.chat.id].vars.keys())
def answer(m):
    poller = pollers[m.chat.id]
    poller(m.text, m.from_user.first_name)
    with open("Cbot_state", mode='wb') as state:
        pickle.dump(pollers, state, protocol=pickle.HIGHEST_PROTOCOL)
    bot.reply_to(m, "Отлично, ваш голос учтен. Чтобы посмотреть результаты, воспользуйтесь командой /results_stat или /results_ind")


@bot.message_handler(content_types=["new_chat_member"])
def newchat(m):
    if m.new_chat_member.id == bot.get_me().id:
        bot.send_message(m.chat.id, "Приветствую!\nПрежде, чем создавать опрос (/createpoll) или тест (/createquiz), " +
                                "убедитесь, что вы начали со мной беседу через личные сообщения")

t = threading.Thread(target=scheduler)
t.daemon = True
t.start()
while True:
    try:
        bot.polling(none_stop=True)
    except exceptions.ReadTimeout or exceptions.ConnectTimeout:
        time.sleep(10)
