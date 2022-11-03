import socket
import threading
import sys

from multiprocessing import Queue
from threading import Lock
from queue import Empty

HOST = ""
PORT = int(sys.argv[1])

NAMES: dict[str, tuple] = {}

CONNECTIONS_POOL = []

lock = Lock()

# trying gracefully exit thread
# https://superfastpython.com/stop-a-thread-in-python/
# https://docs.python.org/2/library/threading.html#threading.Event
event = threading.Event()

def goodbye():
    for name in NAMES.keys():
        sock, addr = NAMES[name]
        sock.close()

def notify_all(names: bytes):
    for name in NAMES.keys():
        sock, addr = NAMES[name]
        sock.sendall(names)

def worker_thread(event: threading.Event, queue: Queue):
    
    client_sock, addr = queue.get()
    name = ''

    data = client_sock.recv(1024)
    data = data.decode()
    name = data
    try:
        if data not in NAMES and not event.is_set():
            if lock.acquire(timeout=1):
                NAMES[data] = (client_sock, addr)
                lock.release()
                names = ' '.join(sorted(NAMES.keys()))
                notify_all(names.encode())
    except KeyboardInterrupt:
        return None
    except Exception:
        return None
    
    try:
        request = client_sock.recv(1024)
        if not request and not event.is_set():
            if lock.acquire(timeout=1):
                del NAMES[name]
                lock.release()
                names = ' '.join(sorted(NAMES.keys()))
                notify_all(names.encode())
    except Exception:
        return None

    client_sock.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(10)
        print("Server started...")

        queue = Queue(10)

        # FIXME
        # workers = [threading.Thread(
        #     target=worker_thread, args=(event, queue,), daemon=False
        # ) for _ in range(10)]
        # for worker in workers:
        #     worker.start()
        workers: list[threading.Thread] = []

        while True:
            try:
                client_sock, addr = sock.accept()
                queue.put((client_sock, addr), True)
                workers.append(threading.Thread(
                    target=worker_thread, args=(event, queue,), daemon=False
                    )
                )
                workers[-1].start()
            except KeyboardInterrupt:
                goodbye()
                event.set()
                for worker in workers:
                    worker.join()
                exit()

if __name__ == "__main__":
    main()
