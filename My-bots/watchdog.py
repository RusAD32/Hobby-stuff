#!/usr/bin/env python3

import socket
import threading
import os, os.path
import time
import subprocess
import shutil
def bot_ls(bot):
    while True:
        compproc = subprocess.run([f"./bots/{bot}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"A problem occured with {bot[:-3]}. See logs")
        with open(f"{bot[:-3]}_errlog", mode = 'a') as log:
            log.write(compproc.stderr.decode("utf-8"))
        dummy = subprocess.run(["./bots/dummy.py", f"{bot}"])
        time.sleep(10)

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
