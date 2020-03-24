#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket

import socket
import struct
import time
import msgpack

class TcpClient(object):
    def __init__(self,ip = '120.76.239.181',port=7003):
        self.ip = ip
        self.port = port
        # 创建socket
        self.address = (self.ip, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.address)
    def send(self, data):
        print(self.socket.send(data))

    def __del__(self):
        self.socket.close()

tm = int(time.time())
msg = {'app_ids': [18001], 'play_types':[1,2,3], 'm_ExclusivePlay':64, 'first_regist': 0, 'm_msgId' : 200000}
msgBody = msgpack.packb(msg)
msgData = struct.pack('HHII', len(msgBody), 100, tm, msg['m_msgId'] * (tm % 10000 + 1)) + msgBody
t = TcpClient()
t.send(msgData)