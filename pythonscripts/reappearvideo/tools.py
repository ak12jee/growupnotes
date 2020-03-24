#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import time
import struct
import traceback
import errno
import msgpack

cfg_userId = [2778969, 2949900, 0, 0]
cfg_ip = '127.0.0.1'
cfg_port = 6001

class TcpClient(object):
    def __init__(self, ip = cfg_ip, port=cfg_port):
        self.ip = ip
        self.port = port
        # 创建socket
        self.address = (self.ip, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.address)
    def send(self, data):
        self.socket.sendall(data)

    def __del__(self):
        self.socket.close()

class Worker(object):
    def __init__(self):
        self.tcpClient = TcpClient()
        self.tm = int(time.time())

    def sendMsg(self, msgUser):
        msg = {'msgId': msgUser['m_msgId'], 'userId': 0, 'data': msgpack.packb(msgUser), 'm_msgId': 186001}
        msgBody = msgpack.packb(msg)
        msgData = struct.pack('HHII', len(msgBody), 100, self.tm, msg['m_msgId'] * (self.tm % 10000 + 1)) + msgBody
        self.tcpClient.send(msgData)

    def sendTuoguan(self):
        msg = {'m_msgId': 186005, 'userId': cfg_userId, 'type': 1}
        self.sendMsg(msg)

    def sendResetDesk(self):
        msg = {'m_msgId': 186006, 'userId': cfg_userId}
        self.sendMsg(msg)

if __name__ == "__main__":
    w = Worker()
    w.sendTuoguan()
    w.sendResetDesk()
