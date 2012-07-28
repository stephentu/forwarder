import struct

# Commands
CMD_NEW_CONN   = 0
CMD_DATA       = 1
CMD_CLOSE_CONN = 2

# read modes
MODE_CMD         = 0
MODE_PAYLOAD_LEN = 1
MODE_PAYLOAD     = 2

# Message formats:
#
# New connection:
# [ CMD_NEW_CONN (1-byte) ]
#
# Data:
# [ CMD_DATA (1-byte) | payload_length (4-bytes) | payload (payload_length bytes) ]
#
# Close connection:
# [ CMD_CLOSE_CONN ]

def create_new_conn_message():
  return struct.pack('B', CMD_NEW_CONN)

def create_data_message(buf):
  '''create a data message, containing buf as the payload'''
  x = struct.pack('BIs', CMD_DATA, len(buf), buf)
  assert len(x) == (1 + 4 + len(buf))

def create_close_conn_message():
  return struct.pack('B', CMD_CLOSE_CONN)
