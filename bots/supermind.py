import random
import sys

class game:
    number = ''
    prev = []
    
    def __init__(self):
        self.prev = []
        self.number = ''.join(random.sample('1234567890', 4))
    
    def __call__(self, guess):
        if guess == self.number:
            return "Правильно! Вы победили!"
        else:
            a, b = 0, 0
            for i in range (0, 4):
                if guess[i] == self.number[i]:
                    a += 1
                elif guess[i] in self.number:
                    b += 1
            self.prev.append((guess, a, b))
            if len(self.prev) == 8:
                return "К сожалению, вы не угадали. Загаданное число: " + self.number
            else:
                return "Цифр на своих позициях: " + str(a) + ";\nПравильных цифр на неверных позициях: " + str(b)

    def guesses_table(self):
        msg = ''
        for attempt in self.prev:
            msg += attempt[0] + " | " + str(attempt[1]) + " | " + str(attempt[2]) + '\n'
        return msg
        
def save(sm_dic):
    with open('./sm', mode = 'w') as sav:
        for x in sm_dic.keys():
            sav.write(str(x) + '\n' + sm_dic[x].number + '\n')
            for attempt in sm_dic[x].prev:
                sav.write(str(attempt) + '\n')
            sav.write('\n')
            
def load():
    with open ("./sm") as sav:
        games = {}
        for gam in sav.read().split('\n\n')[:-1]:
            lines = gam.split('\n')
            pid = int(lines[0])
            sm = game()
            sm.number = lines[1]
            for line in lines[2:]:
                sm.prev.append(eval(line))
            games[pid] = sm
    return games

if __name__ == "__main__":
    sm = game()
    gdict = {1:sm}
    while len(sm.prev) < 8:
        cmnd = input()
        if cmnd[0] == 'p':
            print(sm.guesses_table())
        elif cmnd[0] == 's':
            save(gdict)
        elif cmnd[0] == 'l':
            gdict = load()
            sm = gdict[1]
        elif cmnd.isdigit() and len(cmnd) == 4:
            print(sm(cmnd))
        else:
            print("Введите правильную команду")
