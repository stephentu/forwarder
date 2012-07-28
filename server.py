#!/usr/bin/env python

import select
import socket
import struct
import sys
import threading
import time

import SocketServer

from messages import *

class OutsideListenerHandler(SocketServer.BaseRequestHandler):

  def _write_all(self, s, buf):
    ret = s.sendall(buf)
    assert ret is None

  def handle(self):
    print >>sys.stderr, "INFO: Got outside request"
    s = self.request # s is the external socket

    global ClientSocket
    assert ClientSocket, "no relay connection established"

    # notify ClientSocket of new connection
    self._write_all(ClientSocket, create_new_conn_message())

    client_sock_buf       = '' # holds partially incomplete message (< client_sock_msg_size)
    client_sock_msg_size  = 1 # how long the next message is expected to be
    client_sock_read_mode = MODE_CMD

    while True:
      rlist, _, _ = select.select([s, ClientSocket], [], [])

      for x in rlist:
        if x is s:
          # read all you can currently from s
          try:
            buf = s.recv(8192)
            if not buf:
              # s is closed
              print >>sys.stderr, "INFO: s is closed"
              # notify ClientSocket that the connection is closed
              self._write_all(ClientSocket, create_close_conn_message())
              # shutdown
              s.close()
              # quit handler
              return
            print >>sys.stderr, "INFO: read %d bytes from s - writing to ClientSocket" % len(buf)
            # write it all to ClientSocket
            self._write_all(ClientSocket, create_data_message(buf))
          except socket.error, e:
            print >>sys.stderr, "ERROR: recv(s):", e
            sys.exit(1)
        elif x is ClientSocket:
          # read all you can currently from ClientSocket
          try:
            assert len(client_sock_buf) < client_sock_msg_size, "need bytes to read"
            n = client_sock_msg_size - len(client_sock_buf)
            buf = ClientSocket.recv(n)
            if not buf:
              print >>sys.stderr, "ERROR: ClientSocket is closed - exiting"
              sys.exit(2)
            print >>sys.stderr, "INFO: read %d bytes from ClientSocket" % len(buf)

            client_sock_buf += buf
            assert len(client_sock_buf) <= client_sock_msg_size
            if len(client_sock_buf) == client_sock_msg_size:
              # read entire message
              if client_sock_read_mode == MODE_CMD:
                assert len(client_sock_buf) == 1
                cmd, = struct.unpack('c', client_sock_buf)
                if cmd == CMD_DATA:
                  # switch to reading payload length
                  client_sock_read_mode = MODE_PAYLOAD_LEN
                  client_sock_msg_size = 4
                  client_sock_buf = ''
                elif cmd == CMD_CLOSE_CONN:
                  # the server has closed the connection, so we should
                  # close s
                  s.close()
                  return # exit handler
                else:
                  assert False, "bad command: %d" % cmd
              elif client_sock_read_mode == MODE_PAYLOAD_LEN:
                assert len(client_sock_buf) == 4
                client_sock_read_mode = MODE_PAYLOAD
                client_sock_msg_size, = struct.unpack('I', client_sock_buf)
                assert client_sock_msg_size > 0 # no empty messages
                client_sock_buf = ''
              elif client_sock_read_mode == MODE_PAYLOAD:
                # write the payload to s
                self._write_all(s, client_sock_buf)
                client_sock_read_mode = MODE_CMD
                client_sock_msg_size = 1
                client_sock_buf = ''
              else:
                assert False, 'bad client_sock_read_mode'
          except socket.error, e:
            print >>sys.stderr, "ERROR: recv(ClientSocket):", e
            sys.exit(1)
        else:
          assert False, "bad socket found"

class InsideListenerHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    print >>sys.stderr, "INFO: Got inside request"
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
