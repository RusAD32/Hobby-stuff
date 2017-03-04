#!/usr/bin/env python3.6

import socket
import threading
import os, os.path
import time
import subprocess
import shutil
def bot_ls(bot):
    while True:
        compproc = subprocess.run([f"./bots/{bot}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if compproc.stdout != None and compproc.stdout.decode("utf-8") != '' and int(compproc.stdout.decode("utf-8")) in config.developers:
            ct = time.ctime()
            name = compproc.stdout.decode("utf-8")
            f = open(f"./bots/{bot[:-3]}_blame", mode = 'w')
            f.write(name)
            f.close()
            shutil.copyfile(f'./bots/{bot}', f'./backup/{bot[:-3]} {ct}.py')
            shutil.copyfile(f'./bots/{name}/{bot}', f'./bots/{bot}')
            os.system(f"chmod +x ./bots/{bot}")
        elif compproc.stderr != None and compproc.stderr.decode("utf-8") != '':
            errs = compproc.stderr.decode("UTF-8")
            if "rusad" not in bot:
                with open(f"./{bot[:-3]}_errlog", mode = 'w') as err:
                    err.write(errs)
                print(f"Error with {bot} @ {time.ctime()}, see logs")
                continue
            if "requests.exceptions" in errs or "ApiException" in errs:
                print("disconnected", time.ctime())
                with open(f"./{bot[:-3]}_errlog", mode = 'w') as err:
                    err.write("disconnected")
                time.sleep(10)
                continue
            with open(f"./{bot[:-3]}_errlog", mode = 'w') as err:
                err.write(errs)
            try:
                shutil.copyfile(f'./bots/{bot}', f'./bots/{bot[:-3]}_fail.py')
                shutil.copyfile(f'./backup/{bot[:-3]} {ct}.py', f'./bots/{bot}')
                os.system(f"chmod +x ./bots/{bot}")
                os.remove(f"./backup/{bot[:-3]} {ct}.py")
            except:
                try:
                    shutil.copyfile(f'./bots/{bot[:-3]}_fail.py', f'./bots/{bot}')
                    os.remove(f'./bots/{bot[:-3]}_fail.py')
                    os.system(f"chmod +x ./bots/{bot}")
                except:
                    pass
                dummy = subprocess.run(["./bots/dummy.py"])
            else:
                os.remove(f"./bots/{bot[:-3]}_fail.py")

if __name__ == "__main__":
    files = [file for file in os.listdir("./bots") if "bot.py" in file.lower()]
    for file in files:
        print(file)
        t = threading.Thread(target = bot_ls, args = (file,))
        t.daemon = True
        t.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        exit()
