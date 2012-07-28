#!/usr/bin/env python

import select
import socket
import sys
import threading
import time

import SocketServer

from messages import *

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
  inside_sock = None

  def mk_inside_socket(inside_port):
    x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    x.connect(("localhost", inside_port))
    #x.setblocking(False)
    return x

  # set sockets to be non-blocking
  #outside_sock.setblocking(False)

  out_sock_buf       = ''
  out_sock_msg_size  = 1
  out_sock_read_mode = MODE_CMD

  while True:
    socks = [outside_sock, inside_sock] if inside_sock else [outside_sock]
    rlist, _, _ = select.select(socks, [], [])

    for x in rlist:
      if x is outside_sock:

        assert len(out_sock_buf) < out_sock_msg_size, "need bytes to read"
        n = out_sock_msg_size - len(out_sock_buf)
        # read all you can currently from outside_sock
        buf = outside_sock.recv(n)
        if not buf:
          print >>sys.stderr, "ERROR: outside_sock is closed - exiting"
          sys.exit(2)
        print >>sys.stderr, "INFO: read %d bytes from outside_sock" % len(buf)

        out_sock_buf += buf
        assert len(out_sock_buf) <= out_sock_msg_size
        if len(out_sock_buf) == out_sock_msg_size:
          # read entire message
          if out_sock_read_mode == MODE_CMD:
            assert len(out_sock_buf) == 1
            cmd, = struct.unpack('!B', out_sock_buf)
            if cmd == CMD_DATA:
              # switch to reading payload length
              out_sock_read_mode = MODE_PAYLOAD_LEN
              out_sock_msg_size = 4
              out_sock_buf = ''
            elif cmd == CMD_CLOSE_CONN:
              # the client has closed the connection, so we should
              # close inside_sock
              if inside_sock:
                inside_sock.close()
              inside_sock = None
            elif cmd == CMD_NEW_CONN:
              # this is a new connection, so we should create a new inside_sock
              if inside_sock:
                inside_sock.close()
              inside_sock = mk_inside_socket(inside_port)
            else:
              assert False, "bad command: %d" % cmd
          elif out_sock_read_mode == MODE_PAYLOAD_LEN:
            assert len(out_sock_buf) == 4
            out_sock_read_mode = MODE_PAYLOAD
            out_sock_msg_size, = struct.unpack('!I', out_sock_buf)
            assert out_sock_msg_size > 0 # no empty messages
            out_sock_buf = ''
          elif out_sock_read_mode == MODE_PAYLOAD:
            # write the payload to inside_sock
            assert inside_sock, "payload to write w/o any open socket"
            self._write_all(inside_sock, out_sock_buf)
            out_sock_read_mode = MODE_CMD
            out_sock_msg_size = 1
            out_sock_buf = ''
          else:
            assert False, 'bad out_sock_read_mode'

      elif inside_sock and x is inside_sock:
        # read all you can currently from inside_sock
        buf = inside_sock.recv(8192)
        if not buf:
          print >>sys.stderr, "INFO: inside_sock closed"
          inside_sock.close()
          inside_sock = None
          # notify client
          _write_all(outside_sock, create_close_conn_message())
        else:
          # write it all to outside_sock
          _write_all(outside_sock, create_data_message(buf))
      else:
        assert False, "bad socket found"
