import socket
import sys

SERVER_HOST = sys.argv[1].split(':')[0]
SERVER_PORT = int(sys.argv[1].split(':')[1])
NAME = sys.argv[2]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((SERVER_HOST, SERVER_PORT))

    sock.sendall(str.encode(NAME))
    try:
        while True:
            response = sock.recv(1024)
            response = response.decode()
            if response:
                print(response)
    except KeyboardInterrupt:
        exit()
    