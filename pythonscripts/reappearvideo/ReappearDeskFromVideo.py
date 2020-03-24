#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import time
import struct
import traceback
import errno
import msgpack
import requests
import json

# curl --location --request POST 'http://120.78.21.70:9100/record/v1/getreplay' --data-raw '{"appId":18001,"userId":0,"repalyId":"20200324153639_1_3062_2_4"}'
cfg_url = "http://120.78.21.70:9100/record/v1/getsharereplay"
cfg_appid = 18001
cfg_shareId = 862800
cfg_userId = [2778969, 2949900, 0, 0]
cfg_speed = 1
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
        self.handCard = []
        self.deskCard = []
        self.userId = []
        self.playType = []
        self.oper = []
        self.videoData = None
        self.tcpClient = TcpClient()
        self.msgList = []
        self.tm = int(time.time())
        self.curSendMsgUserId = 2778969
        self.curGetCardPos = None
        self.zhuangPos = None
        self.curSendMsgPos = 0
        self.flagTuoguan = 0

    def getVideoData(self):
        url = cfg_url
        data = {"appId": cfg_appid, "shareId": cfg_shareId}
        res = requests.post(url=url, data=json.dumps(data))
        videoJson = json.loads(res.text)
        if videoJson['errCode'] == 0:
            self.videoData = json.loads(videoJson["data"])
            f = open('data.json','w')
            d = str(self.videoData)            
            f.write(d.replace("\'","\""))
            f.close()
    
    def getVideoDataFromlocal(self):
        f = open('data.json','r')
        d = f.read()
        self.videoData = json.loads(d)
        f.close()

    def parseData(self):
        self.userId = self.videoData['m_userid']
        pt = str(self.videoData['m_strPlayType']).split(';')
        for i in range(len(pt)-1):
            self.playType.append(int(pt[i]))
        cardData = str(self.videoData['m_strData']).split(";")
        curIndex = 0
        for i in range(len(self.userId)):
            c1 = cardData[i].split(',')
            c2 = []
            for i in c1:
                c2.append(int(i))
            self.handCard.append(c2)
            curIndex += 1

        for i in range(curIndex, len(cardData)):
            self.oper.append(cardData[i].split(','))

        for i in self.oper:
            self.parseOperItem(i)
            # print(i)

    def parseOperItem(self, operData):
        '''
        operData 存录像时的格式 [位置,操作,牌]
        '''
        if len(operData) >= 3:
            pos = int(operData[0])
            operType = int(operData[1])
            operCard = []
            o1 = operData[2].split(',')
            for i in o1 :
                if i.find('|') != -1:
                    i1 = i.split('|')
                    operCard.append([int(i1[0]),int(i1[1])])
            if operType == 11:
                c1 = operData[2].split('|')
                c2 = [int(c1[0]), int(c1[1])]
                self.deskCard.append(c2)
                self.curGetCardPos = pos
                if self.zhuangPos == None:
                    self.zhuangPos = pos
            elif operType == 1:
                msg = {'m_msgId': 52, 'm_type': 1, 'm_handCardCount': 0, 'm_think': operCard}
                self.msgList.append([pos, msg])
            elif operType == 102 or operType == 110 or operType == 10 or operType == 5 or operType == 4:
                msg = {'m_msgId': 55, 'm_type': operType % 100, 'm_think': operCard}
                self.msgList.append([pos, msg])
            elif operType == 107 or operType == 7 or operType == 106 or operType == 6 or operType == 109 or operType == 9 or operType == 108 or operType == 8 or operType == 3:
                if operType == 109 or operType == 9:
                    self.sendTuoguan(0)
                msg = {'m_msgId': 52, 'm_type': operType % 100, 'm_handCardCount': 0, 'm_think': operCard}
                self.msgList.append([pos, msg])

    def sendMsg(self, msgUser):
        msg = {'msgId': msgUser['m_msgId'], 'userId': self.curSendMsgUserId, 'data': msgpack.packb(msgUser), 'm_msgId': 186001}
        msgBody = msgpack.packb(msg)
        msgData = struct.pack('HHII', len(msgBody), 100, self.tm, msg['m_msgId'] * (self.tm % 10000 + 1)) + msgBody
        self.tcpClient.send(msgData)

    def sendCfgDesk(self):
        specialCard = []
        for i in self.handCard:
            for j in i:
                specialCard.append(j)
        for i in self.deskCard:
            specialCard.append(i[0])
            specialCard.append(i[1])
        msgUser = {'m_msgId': 186004, 'specialCard': specialCard, 'zhuangPos': self.zhuangPos, 'playType':self.playType}
        self.sendMsg(msgUser)

    def sendOper(self):
        if self.curSendMsgPos >= len(self.msgList):
            print("all oper has send. reset send pos.")
            self.curSendMsgPos = 0
            self.flagTuoguan = 0
            return
        if self.flagTuoguan == 0:
            self.sendTuoguan(1)
            self.flagTuoguan = 1
        self.curSendMsgUserId = cfg_userId[self.msgList[self.curSendMsgPos][0]]
        print("user %d, pos %d, send msg : %s" % (self.curSendMsgUserId,
                                                  self.msgList[self.curSendMsgPos][0], self.msgList[self.curSendMsgPos][1]))
        self.sendMsg(self.msgList[self.curSendMsgPos][1])
        self.curSendMsgPos += 1

    def resetCurSendMsgPos(self):
        self.curSendMsgPos = 0

    def printVideoDataDetail(self):
        if isinstance(self.videoData, dict):
            for key in self.videoData:
                print('%s = %s' % (key, self.videoData[key]))
    def sendTuoguan(self, t = 1):  
        msg = {'m_msgId': 186005, 'userId': cfg_userId, 'type': t}
        self.sendMsg(msg)

    def sendResetDesk(self):
        msg = {'m_msgId': 186006, 'userId': cfg_userId}
        self.sendMsg(msg)

    def printDeskCard(self):
        for i in self.handCard:
            c = []
            for j in range(0, len(i), 2):
                c.append(int(i[j])*10+int(i[j+1]))
            print(c)
        c1 = []
        for i in self.deskCard:
            c1.append(i[0]*10+i[1])
        print(c1)

def cmd(w):
    while True:
        ret = input("--> ")
        ret = ret.split(' ')
        if ret[0] == 'exit':
            break
        elif ret[0] == 'deskcard':
            w.printDeskCard()  
        elif ret[0] == 'cfg':
            w.sendCfgDesk() 
        elif ret[0] == 'tuoguan':
            if len(ret) < 2:
                continue
            w.sendTuoguan(int(ret[1]))  
        elif ret[0] == 'reset':
            w.sendResetDesk()
        elif ret[0] == 'n' or ret[0] == 'sendoper':
            w.sendOper()
        elif ret[0] == 'resetMsgPos':
            w.resetCurSendMsgPos()
        elif ret[0] == 'h':
            print('''
Usage :
    exit
    cfg
    deskcard
    tuoguan
    reset
    n or sedoper
    resetMsgPos
    h --help
            ''')

if __name__ == "__main__":
    w = Worker()
    w.getVideoDataFromlocal()
    # w.printVideoDataDetail()
    print("get video success.")
    w.parseData()
    cmd(w)