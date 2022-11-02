import socket
import threading
import sys

import time

from multiprocessing import Queue
from threading import Lock

HOST = ""
PORT = int(sys.argv[1])

NAMES: dict[str, tuple] = {}

CONNECTIONS_POOL = []

lock = Lock()

def goodbye():
    for name in NAMES.keys():
        sock, addr = NAMES[name]
        sock.close()

def notify_all(names: bytes):
    for name in NAMES.keys():
        sock, addr = NAMES[name]
        sock.sendall(names)

def worker_thread(queue):
    client_sock, addr = queue.get()
    name = ''

    data = client_sock.recv(1024)
    data = data.decode()
    name = data
    try:
        if data not in NAMES:
            lock.acquire()
            NAMES[data] = (client_sock, addr)
            lock.release()
            names = ' '.join(sorted(NAMES.keys()))
            notify_all(names.encode())
    except KeyboardInterrupt:
        return None
    except:
        return None
    
    try:
        request = client_sock.recv(1024)
        if not request:
            lock.acquire()
            del NAMES[name]
            lock.release()
            names = ' '.join(sorted(NAMES.keys()))
            notify_all(names.encode())
    except:
        return None

    client_sock.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(10)
        print("Server started...")

        queue = Queue(10)

        workers = [threading.Thread(
            target=worker_thread, args=(queue,), daemon=False
        ) for _ in range(10)]
        for worker in workers:
            worker.start()

        while True:
            try:
                client_sock, addr = sock.accept()
                queue.put((client_sock, addr), True)
            except KeyboardInterrupt:
                goodbye()
                exit()

if __name__ == "__main__":
    main()