#!/usr/bin/env python

import select
import socket
import sys
import threading
import time

import SocketServer

def _write_all(s, buf):
  ret = s.sendall(buf)
  assert ret is None

if __name__ == '__main__':
  prog, outside_host, outside_port, inside_port = sys.argv
  outside_port = int(outside_port) # the application port
  inside_port  = int(inside_port)  # an internal port

  # make TCP connection to outside_host:outside_port
  outside_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  outside_sock.connect((outside_host, outside_port))

  # make TCP connection to localhost:inside_port
  inside_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  inside_sock.connect(("localhost", inside_port))

  BufSize = 4096

  # set sockets to be non-blocking
  outside_sock.setblocking(False)
  inside_sock.setblocking(False)

  while True:
    rlist, _, _ = select.select([outside_sock, inside_sock], [], [])

    for x in rlist:
      if x is outside_sock:
        # read all you can currently from outside_sock
        try:
          buf = outside_sock.recv(BufSize)
          # write it all to inside_sock
          _write_all(inside_sock, buf)
        except socket.error, e:
          print >>sys.stderr, "ERROR: recv(outside_sock):", e
      elif x is inside_sock:
        # read all you can currently from inside_sock
        try:
          buf = inside_sock.recv(BufSize)
          # write it all to outside_sock
          _write_all(outside_sock, buf)
        except socket.error, e:
          print >>sys.stderr, "ERROR: recv(inside_sock):", e
      else:
        assert False, "bad socket found"
