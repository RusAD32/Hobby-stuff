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
        s = compproc.stderr.decode("utf-8")
        if len(s) > 5:
            with open(f"{bot[:-3]}_errlog", mode = 'a') as log:
                log.write(s)
                dummy = subprocess.run(["./bots/dummy.py", f"{bot}"])
        time.sleep(10)

if __name__ == "__main__":
    files = [file for file in os.listdir("./bots") if "bot.py" in file.lower()]
    for file in files:
        print(file)
        t = threading.Thread(target = bot_ls, args = (file,))
        t.daemon = True
        t.start()
    updater = socket.socket()
    updater.bind( ("", 11111) )
    updater.listen(1)
    try:
        while True:
            conn, addr = updater.accept()
            data = conn.recv(1024)
            if data == b"reset":
                ps = subprocess.check_output(["ps", "-ef"]).decode("utf-8")
                procs = ps.split('\n')
                pids = []
                for line in [x for x in procs if "bot" in x]:
                    print(line)
                    items = line.split('\t')
                    if "grep" not in procs:  # I was too lazy to count...
                        pids.append(items[1])
                for pid in pids:
                    os.system(f"kill {pid}")
            conn.close()
            time.sleep(10)
    except KeyboardInterrupt:
        exit()
