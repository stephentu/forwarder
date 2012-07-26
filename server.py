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
    print >>sys.stderr, "WARN: Got outside request"
    s = self.request

    global ClientSocket
    assert ClientSocket

    BufSize = 4096

    # set sockets to be non-blocking
    #s.setblocking(False)
    #ClientSocket.setblocking(False)

    while True:
      rlist, _, _ = select.select([s, ClientSocket], [], [])

      for x in rlist:
        if x is s:
          # read all you can currently from s
          try:
            buf = s.recv(BufSize)
            if not buf:
              # s is closed
              print >>sys.stderr, "INFO: s is closed"
              return
            print >>sys.stderr, "INFO: read %d bytes from s - writing to ClientSocket" % len(buf)
            # write it all to ClientSocket
            self._write_all(ClientSocket, buf)
          except socket.error, e:
            print >>sys.stderr, "ERROR: recv(s):", e
            sys.exit(1)
        elif x is ClientSocket:
          # read all you can currently from ClientSocket
          try:
            buf = ClientSocket.recv(BufSize)
            if not buf:
              print >>sys.stderr, "ERROR: ClientSocket is closed - exiting"
              sys.exit(2)
            print >>sys.stderr, "INFO: read %d bytes from ClientSocket" % len(buf)
            # write it all to s
            self._write_all(s, buf)
          except socket.error, e:
            print >>sys.stderr, "ERROR: recv(ClientSocket):", e
            sys.exit(1)
        else:
          assert False, "bad socket found"


class InsideListenerHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    print >>sys.stderr, "WARN: Got inside request"
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

  out_srvr = SocketServer.TCPServer(("0.0.0.0", outside_port), OutsideListenerHandler)
  in_srvr  = SocketServer.TCPServer(("0.0.0.0", inside_port),  InsideListenerHandler)

  out_srvr_thd = threading.Thread(target=out_srvr.serve_forever)
  out_srvr_thd.start()

  in_srvr_thd = threading.Thread(target=in_srvr.serve_forever)
  in_srvr_thd.start()

  out_srvr_thd.join()
  in_srvr_thd.join()
