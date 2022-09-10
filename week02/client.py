import socket
import sys

HOST, PORT = sys.argv[1].split(':')

numbers = [
    15492781, 15492787, 15492803
    # 15492811, 15492810, 15492833,
    # 15492859, 15502547, 15520301,
    # 15527509, 15522343, 1550784
    ]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, int(PORT)))

    sock.sendall(str.encode('\n'.join([str(number) for number in numbers])))
    chunk = sock.recv(1024)
    data = chunk.decode().split('\n')
    print(*data, sep='\n')
    print('Completed')
    exit()