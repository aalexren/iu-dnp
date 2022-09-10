from multiprocessing import Queue

import socket
import threading
import sys, time


def worker(queue):
    while True:
        client_sock, addr = queue.get()
        with client_sock:
            print(f'{addr} client is connected')
            data = client_sock.recv(1024)
            numbers = list(map(int, data.decode().split('\n')))
            ans = []
            for number in numbers:
                res = is_prime(number)
                res = f'{number} is ' + 'not ' * (not res) + 'prime'
                ans.append(res)
            client_sock.sendall('\n'.join(ans).encode())
            print(f'{addr} is disconnected')
            

def is_prime(n: int) -> bool:
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for divisor in range(3, n, 2):
        if n % divisor == 0:
            return False
    return True


def main():
    PORT = int(sys.argv[1])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', PORT))
        sock.listen(5) # size of the queue to connect, refuse new if maximum is reached

        queue = Queue(10)

        for _ in range(5):
            t = threading.Thread(target=worker, args=(queue,), daemon=True)
            t.start()

        while True:
            try:
                client_sock, addr = sock.accept()
                queue.put((client_sock, addr,), True, None) # wait for the free slot
            except KeyboardInterrupt:
                print('Shutting down')
                print('Done')
                exit()


if __name__ == '__main__':
    main()