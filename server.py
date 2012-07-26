#!/usr/bin/env python

import select
import socket
import sys
import threading
import time

import SocketServer

class OutsideListenerHandler(SocketServer.BaseRequestHandler):

  def _write_all(self, s, buf):
    ret = s.sendall(buf)
    assert ret is None

  def handle(self):
    s = self.request

    global ClientSocket
    assert ClientSocket

    BufSize = 4096

    # set sockets to be non-blocking
    s.setblocking(False)
    ClientSocket.setblocking(False)

    while True:
      rlist, _, _ = select.select([s, ClientSocket], [], [])

      for x in rlist:
        if x is s:
          # read all you can currently from s
          try:
            buf = s.recv(BufSize)
            # write it all to ClientSocket
            self._write_all(ClientSocket, buf)
          except socket.error, e:
            print >>sys.stderr, "ERROR: recv(s):", e
        elif x is ClientSocket:
          # read all you can currently from ClientSocket
          try:
            buf = ClientSocket.recv(BufSize)
            # write it all to s
            self._write_all(s, buf)
          except socket.error, e:
            print >>sys.stderr, "ERROR: recv(ClientSocket):", e
        else:
          assert False, "bad socket found"


class InsideListenerHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    s = self.request

    # XXX: do something better than this
    global ClientSocket
    ClientSocket = s
    while True:
      time.sleep(10)

if __name__ == '__main__':
  prog, outside_port, inside_port = sys.argv
  outside_port = int(outside_port) # the application port
  inside_port  = int(inside_port)  # an internal port
  assert outside_port != inside_port, "app port / internal port should not be the same"

  out_srvr = SocketServer.TCPServer(("localhost", outside_port), OutsideListenerHandler)
  in_srvr  = SocketServer.TCPServer(("localhost", inside_port),  InsideListenerHandler)

  out_srvr_thd = threading.Thread(target=out_srvr.serve_forever)
  out_srvr_thd.start()

  in_srvr_thd = threading.Thread(target=in_srvr.serve_forever)
  in_srvr_thd.start()

  out_srvr_thd.join()
  in_srvr_thd.join()
