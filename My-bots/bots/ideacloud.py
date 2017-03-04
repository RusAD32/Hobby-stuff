class Workspace:
    name = ''
    leaders = []
    users = []

    def __init__(self, name):
        self.name = name

    def add_user(self, user_id):
        if not user_id in self.users:
            self.users.append(user_id)

    def add_leader(self, user_id):
        if not user_id in self.users:
            self.users.append(user_id)
        if not user_id in self.leaders:
            self.leaders.append(user_id)

    def remove_leader(self, user_id):
        if user_id in self.leaders:
            self.leaders.remove(user_id)

    def remove_user(self, user_id):
        if user_id in self.leaders:
            self.leaders.remove(user_id)
        if user_id in self.users:
            self.users.remove(user_id)

def save(wds, fpath):
    with open(fpath, mode = 'w') as sav:
        for wd in wds:
            sav.write(wd.name + '\n')
            sav.write(str(wd.leaders) + '\n')
            sav.write(str(wd.users) + '\n\n')

def load(fpath):
    res = {}
    with open(fpath) as sav:
        wss = sav.read().split('\n\n')[:-1]
        for unit in wss:
            fields = unit.split('\n')
            ws = Workspace(fields[0])
            ws.leaders = eval(fields[1])
            ws.users = eval(fields[2])
            res[fields[0]] = ws
    return res
