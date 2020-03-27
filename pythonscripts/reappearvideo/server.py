#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import time
import struct
import msgpack

# 创建socket
tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
address = ('', 6001)
tcp_server_socket.bind(address)
tcp_server_socket.listen(128)
client_socket, clientAddr = tcp_server_socket.accept()
recv_data = client_socket.recv(1024*4)
print("recv len ", len(recv_data))
s = struct.unpack("HHII",recv_data[:12])

print("msgId %d" % (s[3] / (s[2] % 10000 + 1)))
print(type(s))

s1 = msgpack.unpackb(recv_data[12:])
print(type(s1),s1)