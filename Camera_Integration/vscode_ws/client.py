# win_client.py
import socket
import struct

HOST = "192.168.0.171"
PORT = 5000

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b"hello", (HOST, PORT))

while True:
    data, addr = s.recvfrom(4096)
    if len(data) < 4:
        continue
    length = struct.unpack("!I", data[:4])[0]
    if len(data) < 4 + length:
        continue
    message = data[4:4+length]
    print("Received:", message)
