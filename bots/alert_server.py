#!/usr/bin/env python3

from reminder_pb2 import reminder
import threading
import socket
import time
import os, os.path

def send_alerts(data):
    time.sleep(data.ttw)
    print("waited")
    while True:
        try:
            sender = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sender.connect("./sender")
            print("connected")
            sender.send(data.SerializeToString())
            print("sent")
            sender.close()
            break
        except:
            time.sleep(10)
    
if os.path.exists("./alerts"):
    os.remove("./alerts")

alerter = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
alerter.bind("./alerts")
alerter.listen(1)

while True:
    conn, addr = alerter.accept()
    data = reminder()
    data.ParseFromString(conn.recv(8192))
    alert = threading.Thread(target = send_alerts, args = (data,))
    alert.start()
    conn.close()
        


        
    
