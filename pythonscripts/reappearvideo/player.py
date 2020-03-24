#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import uuid
import random
import threading

import HttpClient
from tcp_client import *


class PlayerState(object):
    PLAYER_STATE_INIT = 0
    PLAYER_STATE_USER_CENTER_LOGINED = 0x01
    PLAYER_STATE_GAME_LOGINED = 0x02
    PLAYER_STATE_ASSET_OK = 0x04
    PLAYER_STATE_PING_SEND = 0x08
    PLAYER_STATE_PONG_RECV = 0x10
    PLAYER_STATE_MSG_RECV = 0x40
    PLAYER_STATE_ON_DESK = 0x80
    PLAYER_STATE_ERROR = 0x0100


mapServerName = ['A1 ', 'A2 ', 'B ']


class Player(object):
    msgHandlers = {}

    def __init__(self, serverIndex = None, epoll = None, logger = None):
        self.openId = 1245
        self.serverIndex = serverIndex
        self.epoll = epoll
        self.id = 0
        self.gid = 0
        self.accessToken = ""
        self.refreshToken = ""
        self.tcpClient = None
        self.lastSendMsg = None
        self.lastRecvMsgs = []
        self.lastSendMsgs = []
        self.state = PlayerState.PLAYER_STATE_INIT
        self.step = 0
        self.loopsBeforeNextPing = 0
        self.sleepLoops = 0
        self.pos = 0
        self.handlerContext = {}

    def SetStep(self, step):
        self.step = step

    def HasSend(self, msgId):
        return self.lastSendMsg and self.lastSendMsg['m_msgId'] == msgId

    def HasRecv(self, msgId, step):
        for rm in reversed(self.lastRecvMsgs):
            if rm["step"] < step:
                return False
            if rm["step"] == step and rm["msg"]["m_msgId"] == msgId:
                return True
        return False

    def GetLastRecv(self, msgId, step):
        for rm in reversed(self.lastRecvMsgs):
            if rm["step"] < step:
                return None
            if rm["step"] == step and rm["msg"]["m_msgId"] == msgId:
                return rm["msg"]
        return None

    def GetRecvCount(self, msgId, step):
        count = 0
        for rm in reversed(self.lastRecvMsgs):
            if rm["step"] < step:
                break
            if rm["step"] == step and rm["msg"]["m_msgId"] == msgId:
                count += 1
        return count

    def GetAllRecv(self, step):
        recvs = []
        for rm in reversed(self.lastRecvMsgs):
            if rm["step"] < step:
                break
            if rm["step"] == step:
                recvs.append(rm["msg"])
        return recvs

    def GetCurRecv(self):
        recvs = []
        step = -1
        for rm in reversed(self.lastRecvMsgs):
            print("getCurRecv, read lastRecvMsgs=" + str(rm))
            if step == -1:
                step = rm["step"]
            elif rm["step"] != step:
                break
            recvs.append(rm["msg"])
        return recvs

    def ClearAllRecv(self):
        self.lastSendMsgs = []
        self.lastRecvMsgs = []

    def ClearError(self):
        self.state &= ~PlayerState.PLAYER_STATE_ERROR

    # 登录用户中心
    def LoginUserCenter(self):
        self.state &= ~PlayerState.PLAYER_STATE_USER_CENTER_LOGINED
        result = HttpClient.HttpClient.get(
            headers={
            "X-QP-AppId": str(18001),
            "X-QP-Timestamp": str(int(time.time())),
            "X-QP-Nonce": "%s" % uuid.uuid1()
            },
            url="http://120.78.87.250:8001" + "/uc/v1/login/local",
            params={
            "appId": str(18001),
            "openId": str(self.openId),
            "deviceId": "%s" % uuid.uuid1(),
            "deviceType": 2
        })

        if result is None or result["errCode"] != 0:
            if result is not None:
                print("login user center failed, error code " + str(result["errCode"]))
            return

        self.accessToken = result["data"]["accessToken"]
        self.refreshToken = result["data"]["refreshToken"]
        self.gid = int(result["data"]["gid"])
        self.id = int(result["data"]["userId"])
        self.state |= PlayerState.PLAYER_STATE_USER_CENTER_LOGINED

    def SendMsg(self, msg):
        # print("发送的消息msg=" + str(msg))
        if not self.tcpClient.SendMsg(msg):
            self.sleepLoops = 2 + random.randint(0, 3)  # 200~500 ms
            return False

        if msg and msg["m_msgId"] != 15:
            self.lastSendMsg = msg
            self.lastSendMsgs.append({"msg": msg, "step": self.step})
            self.state &= ~PlayerState.PLAYER_STATE_MSG_RECV
            print("send " + str(msg["m_msgId"]) + " on step " + str(self.step))
        return True

    def LoginGame(self):  # 链接Gate 登录
        if self.HasSend(8):
            return

        self.state &= ~PlayerState.PLAYER_STATE_GAME_LOGINED
        if self.tcpClient is None or self.tcpClient.connectState != ConnectState.CONNECT_STATE_CONNECT_OK:
            if self.tcpClient:
                self.tcpClient.Close()
            # print("Player.MsgHandler=" + str(Player.MsgHandler))
            self.tcpClient = TCPClient(Player.MsgHandler, self)  # 连接gate

        self.lastSendMsg = None
        if not self.tcpClient.Connect('10.150.89.224:8011'):
            print("connect " + '10.150.89.224:8011' + " failed, sleep 1000 loops")
            self.sleepLoops = 10  # 1000 ms
            return

        self.sleepLoops = 0
        print("connect socket no " + str(self.tcpClient.socket.fileno()))
        self.SendMsg({
            'm_userId': self.gid,
            'm_gid': self.gid,
            'm_accessToken': self.accessToken,
            'm_msgId': 8,
        })

    def Login(self):
        if not self.state & PlayerState.PLAYER_STATE_USER_CENTER_LOGINED or self.gid == 0:
            self.LoginUserCenter()
        if self.state & PlayerState.PLAYER_STATE_USER_CENTER_LOGINED:
            self.LoginGame()  # 登录服务器

    def Logout(self):  # 退出,下线
        socket_no = 0
        if self.tcpClient:
            self.tcpClient.Close()
        self.tcpClient = None
        print('Logout Successfully, socket no ' + str(socket_no))
        self.state &= ~(PlayerState.PLAYER_STATE_GAME_LOGINED | PlayerState.PLAYER_STATE_ERROR)
        self.lastSendMsg = None
        self.gid = 0
        self.id = 0

    def CreateDesk(self, create_desk_msg):
        self.state &= ~PlayerState.PLAYER_STATE_ON_DESK
        if self.SendMsg(create_desk_msg):
            print('create table send')
            return True

        return False

    def MsgHandler(self, recvMsg):
        # print("recvMsg=" + str(recvMsg))
        msgId = recvMsg['m_msgId']

        if msgId != 16:
            self.state |= PlayerState.PLAYER_STATE_MSG_RECV
            self.lastRecvMsgs.append({"msg": recvMsg, "step": self.step})
            print("!!!!!add lastRecvMsgs, msg=" + str(recvMsg) + ", step=" + str(self.step))

        print("Player.msgHandlers.keys:" + str(Player.msgHandlers.keys()))
        if Player.msgHandlers.has_key(msgId):
            handlers = Player.msgHandlers[msgId]
            # print("handlers=" + str(handlers))
            for i in range(len(handlers)-1, -1, -1):
                context = handlers[i]["context"]
                # print("context=" + str(context))
                if context == "player":
                    if handlers[i]["handler"](self, recvMsg):
                        return
                else:
                    if self.handlerContext.has_key(context):
                        if handlers[i]["handler"](self.handlerContext[context], self, recvMsg):
                            return

        if Player.msgHandlers.has_key(-1):
            handlers = Player.msgHandlers[-1]
            for i in range(len(handlers) - 1, -1, -1):
                context = handlers[i]["context"]
                if context == "player":
                    if handlers[i]["handler"](self, recvMsg):
                        return
                else:
                    if self.handlerContext.has_key(context):
                        if handlers[i]["handler"](self.handlerContext[context], self, recvMsg):
                            return

    def OnLoginGame(self,  recvMsg):
        # TODO
        msgId = recvMsg['m_msgId']
        if msgId == 9:
            errCode = recvMsg['m_errCode']
            if errCode != 0:
                print("check token falied, error code " + str(errCode))
                if errCode == 1003 or errCode == 1004:
                    self.LoginUserCenter()
                    return True
            else:
                print("check token success")

            self.SendMsg({
                'm_id': self.gid,
                'm_nAppId': 18001,
                'm_localId': self.id,
                'm_msgId': 11,
            })
            self.loopsBeforeNextPing = 30  # 3000ms
            print(" begin login")
            return True

        if msgId == 12:
            errCode = int(recvMsg['m_errorCode'])
            if errCode != 0:
                print("login falied, error code " + str(errCode))
                self.LoginUserCenter()
                return True

            if recvMsg["m_state"] != 0 and not (self.state & PlayerState.PLAYER_STATE_ON_DESK):
                self.ReconnectWithNewOpenId("user on desk already, retry with openId ")
                return True

            print("login success")
            self.state |= PlayerState.PLAYER_STATE_GAME_LOGINED

    def OnHeartbeat(self, recvMsg):
        self.state |= PlayerState.PLAYER_STATE_PONG_RECV
        return True

    def OnDeskCreate(self, result):
        print("=====OnDeskCreate===result=" + str(result))
        if result == "OK":
            self.state |= PlayerState.PLAYER_STATE_ON_DESK
            return True

        self.lastSendMsg = {"m_msgId": 11}
        print("create desk failed, result " + result)
        if result == "DELAY":
            self.sleepLoops = 10  # 1000 ms
            return True

        if result == "REPLACE":     # 此号无房卡或已经在桌子上，换一个试试
            self.ReconnectWithNewOpenId("create desk failed, retry with openId ")

        return True

    def OnDeskAdd(self, result):
        print("=======onDeskAdd========result=" + str(result))
        if result == "OK":
            self.state |= PlayerState.PLAYER_STATE_ON_DESK
        elif result == "ERROR-FULL":
            self.state |= PlayerState.PLAYER_STATE_ERROR
        else:
            print("add desk failed, result " + result)
        return True

    def OnDeskDel(self, result):
        print("======OnDeskDel=====result=" + str(result))
        if result == "OK":
            self.state &= ~PlayerState.PLAYER_STATE_ON_DESK
            print("leave desk")

        return True

    def Cron(self, loops_elapse):
        # print("loops_elapse=" + str(loops_elapse) + ", sleepLoops=" + str(self.sleepLoops))  # loops_elapse=0, sleepLoops=0
        if self.sleepLoops > 0:
            if self.sleepLoops < loops_elapse:
                self.sleepLoops = 0
            else:
                self.sleepLoops -= loops_elapse
        # print("loops_elapse=" + str(loops_elapse) + ", sleepLoops=" + str(self.sleepLoops))
        if not self.state & PlayerState.PLAYER_STATE_GAME_LOGINED:
            # print("loopsBeforeNextPing=" + str(self.loopsBeforeNextPing))
            self.loopsBeforeNextPing -= loops_elapse
            if self.HasSend(11) and self.loopsBeforeNextPing <= 0:
                self.lastSendMsg = None
            return

        if self.loopsBeforeNextPing <= 0:
            self.SendMsg({'m_msgId': 15})
            self.state |= PlayerState.PLAYER_STATE_PING_SEND
            self.state &= ~PlayerState.PLAYER_STATE_PONG_RECV
            self.loopsBeforeNextPing = 20 + random.randint(-10, 10)
        else:
            self.loopsBeforeNextPing -= loops_elapse
        # print("loopsBeforeNextPing=" + str(self.loopsBeforeNextPing))

    def NeedReconnect(self):
        if not self.tcpClient or self.tcpClient.HasError():
            return True
        if self.state & PlayerState.PLAYER_STATE_GAME_LOGINED:
            return False
        if self.state & PlayerState.PLAYER_STATE_USER_CENTER_LOGINED and (self.HasSend(8) or self.HasSend(11)):
            return False

        return True

    def ReconnectWithNewOpenId(self, logMsg):
        self.Logout()
        openId = 100001
        print(logMsg + str(openId))
        self.openId = openId
        self.lastRecvMsgs = []
        self.step = 0
        self.state = PlayerState.PLAYER_STATE_INIT
        self.Login()

    @staticmethod
    def RegisterMsgHandler(msgId, context, handler):
        if msgId not in Player.msgHandlers:
            Player.msgHandlers[msgId] = []
        Player.msgHandlers[msgId].append({"handler": handler, "context": context})

    @staticmethod
    def RegisterAllMsgHandler():
        # TODO
        Player.RegisterMsgHandler(9, "player", Player.OnLoginGame)
        Player.RegisterMsgHandler(12, "player", Player.OnLoginGame)
        Player.RegisterMsgHandler(16, "player", Player.OnHeartbeat)
