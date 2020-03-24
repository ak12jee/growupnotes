#!/usr/bin/python
# -*- coding: UTF-8 -*-
import binascii
# import hashlib
import random

import socket
import time
import struct
import traceback
import errno
import msgpack
from Queue import Queue

class ConnectState(object):
    CONNECT_STATE_CONNECT_OK = 0
    CONNECT_STATE_UNCONNECT = 1
    CONNECT_STATE_RECONNECT_PADDING = 2


class TCPClient(object):
    # asyncIO = AsyncIO()

    def __init__(self, msgHandler, player, async=False):
        self.socket = None
        self.connectState = ConnectState.CONNECT_STATE_UNCONNECT
        self.msgHandler = msgHandler
        self.player = player
        self.recvBuffer = bytes()
        self.stop = False
        self.addr = None
        self.sendQueue = Queue()
        self.recvQueue = Queue()
        self.async = async
        self.socketNo = 0

    def HasRecv(self):
        return not self.recvQueue.empty()

    def HasError(self):
        return self.connectState == ConnectState.CONNECT_STATE_RECONNECT_PADDING

    def Connect(self, addr):
        if self.connectState == ConnectState.CONNECT_STATE_CONNECT_OK:
            return True

        self.addr = addr
        try:
            s = str.split(addr, ":")
            if self.socket:
                # if self.async:
                #     TCPClient.asyncIO.Remove(self)
                self.Close()

            self.recvBuffer = bytes()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((s[0], int(s[1])))
            self.socket.setblocking(False)
            self.socketNo = self.socket.fileno()
            self.stop = False
        except Exception, e:
            self.player.LogError("connect " + addr + " Failed!! " + str(e))
            self.connectState = ConnectState.CONNECT_STATE_RECONNECT_PADDING
            return False

        self.connectState = ConnectState.CONNECT_STATE_CONNECT_OK
        return True

    def Stop(self):
        self.stop = True

    def Close(self):
        self.Stop()
        if self.socket:
            # if self.async:
            #     TCPClient.asyncIO.Remove(self)
            self.player.LogDebug("close socket no " + str(self.socket.fileno()))
            if self.socketNo != 0:
                self.player.epoll.unregister(self.socketNo)
                self.socketNo = 0
            self.socket.close()
            self.socket = None
        if self.connectState != ConnectState.CONNECT_STATE_UNCONNECT:
            self.connectState = ConnectState.CONNECT_STATE_UNCONNECT

    def CheckState(self):
        if self.connectState == ConnectState.CONNECT_STATE_UNCONNECT:
            return False
        elif self.connectState == ConnectState.CONNECT_STATE_RECONNECT_PADDING:
            return False
        return True

    def SendMsg(self, msg):  # 消息处理后发送
        if not self.CheckState():
            return False

        if self.async:
            self.sendQueue.put(msg)
            return True
        else:
            return self.OnSend(msg)

    def OnSend(self, msg_send=None):
        if not self.async and not msg_send:
            return True

        while not self.stop and self.socket:
            msg = msg_send
            if not msg and not self.sendQueue.empty():
                try:
                    msg = self.sendQueue.get_nowait()
                except:
                    pass
            if not msg:
                return True

            try:
                msgBody = msgpack.packb(msg)
                tm = int(time.time())
                msg_data = struct.pack("HHII", len(msgBody), 100, tm, msg["m_msgId"] * (tm % 10000 + 1)) + msgBody
                self.socket.sendall(msg_data)

                if msg_send:
                    return True
            except Exception, e:
                self.connectState = ConnectState.CONNECT_STATE_RECONNECT_PADDING
                self.player.LogError("send failed : " + str(e))
                traceback.print_exc()
                return False

    def RecvMsg(self):
        if not self.CheckState():
            return False
        print("async=" + str(self.async))
        if not self.async:
            return self.OnRecv()

        while not self.recvQueue.empty():
            try:
                msg = self.recvQueue.get_nowait()
                print("从接收消息队列获取消息，msg=" + str(msg))
            except:
                return True
            if not msg:
                return True

            try:
                print("=======enter msgHandler==========")
                self.msgHandler(self.player, msg)
            except Exception, e:
                self.player.LogError("msg handler Failed!! msg: " + str(msg) + ', exception: ' + str(e))
                return False

        return True

    def OnRecv(self):
        while not self.stop and self.socket:
            try:
                recv = self.socket.recv(4096)
                if not recv or len(recv) == 0:
                    return True

                self.recvBuffer += recv
                while not self.stop:
                    if len(self.recvBuffer) < 12:
                        break
                    head = struct.unpack('HHII', self.recvBuffer[:12])
                    bodySize = head[0]
                    if len(self.recvBuffer) < 12 + bodySize:
                        break
                    body = self.recvBuffer[12:(12 + bodySize)]

                    try:
                        recvMsg = msgpack.unpackb(body)
                        if not self.async:
                            self.msgHandler(self.player, recvMsg)
                        else:
                            self.recvQueue.put(recvMsg)
                    except Exception, e:
                        self.player.LogError("msg handler Failed!! msg: " + str(body) + ', exception: ' + str(e))
                        traceback.print_exc()
                    finally:
                        self.recvBuffer = self.recvBuffer[12 + bodySize:]
            except socket.timeout:
                pass
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    return True
                self.player.LogError("recv failed : " + str(e))
                self.connectState = ConnectState.CONNECT_STATE_RECONNECT_PADDING
                return False
            except Exception, e:
                self.player.LogError("recv failed: " + str(e))
                self.connectState = ConnectState.CONNECT_STATE_RECONNECT_PADDING
                return False

            return True

