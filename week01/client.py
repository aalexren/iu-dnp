import os
import argparse
import socket
import select

class Config:
    def __init__(self):
        self._config = {}
        self._set_cli_args()
    
    @property
    def hostname(self) -> str:
        return self._hostname

    @property
    def port(self) -> int:
        return self._port

    @property
    def lfile(self) -> str:
        return self._lfile

    @property
    def rfile(self) -> str:
        return self._rfile

    def _set_cli_args(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('address', nargs='+', help='<ip address>:<port>')
        self.parser.add_argument('lfile', nargs='+', help='local filename')
        self.parser.add_argument('rfile', nargs='+', help='remote filename')
        args = self.parser.parse_args()
        
        self._hostname = args.address[0].split(':')[0]
        self._port = int(args.address[0].split(':')[1])
        self._lfile = args.lfile[0]
        self._rfile = args.rfile[0]

    def __repr__(self) -> str:
        return f'{self._hostname}:{self._port} {self._lfile} -> {self._rfile}'


class Client:
    def __init__(self, config: Config):
        self.config = config
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._buf_size = 1024
        self._total_size = os.stat(self.config.lfile).st_size # file size in bytes
        self._seqno = 0
    
    def send_file(self):
        self._start_message()
        self._data_message_loop()
        print('File has been transmitted successfully!')

    def _start_message(self):
        packet = self.__format_start_packet(self._seqno)
        response = self.__send_start_message(packet)
        prefix, n_seqno, buf_size = response.split(' | '.encode())
        self._seqno = int(n_seqno.decode())
        self._buf_size = int(buf_size.decode())

    def __send_start_message(self, packet: bytes) -> bytes:
        for attempt in range(1, 6):
            self.socket.sendto(packet, (self.config.hostname, self.config.port,))
            if (response := self.__get_start_response(attempt)) != None:
                print(f'Retrieved ack for start message for seqno #{self._seqno}')
                return response
        raise TimeoutError()

    def __get_start_response(self, attempt: int):
        readable, _, _ = select.select([self.socket], [], [], 0.5)
        if readable:
            return readable[0].recv(1024)
        else:
            print(f'Wait for ack message for seqno #{self._seqno} attempt {attempt}...')
            return None

    def _data_message_loop(self):
        with open(self.config.lfile, 'rb') as f:
            while chunk := f.read(self._buf_size - 44): # 44 occupied by signature of the message
                print(f'Send packet with seqno #{self._seqno}')
                packet = self.__format_data_packet(self._seqno, chunk)
                response = self.__send_data_message(packet)
                prefix, n_seqno = response.split(' | '.encode())
                self._seqno = int(n_seqno.decode())

    def __send_data_message(self, packet: bytes) -> bytes:
        for attempt in range(1, 6):
            self.socket.sendto(packet, (self.config.hostname, self.config.port,))
            if (response := self.__get_data_response(attempt)) != None:
                print(f'Retrieved ack message for seqno #{self._seqno}')
                return response
        raise TimeoutError()

    def __get_data_response(self, attempt: int):
        readable, _, _ = select.select([self.socket], [], [], 0.5)
        if readable:
            return readable[0].recv(1024)
        else:
            print(f'Wait for ack message for seqno #{self._seqno} attempt {attempt}...')
            return None
    
    def __format_start_packet(self, seqno: int):
        return f"s | {seqno} | {self.config.rfile} | {self._total_size}".encode()

    def __format_data_packet(self, seqno: int, data: bytes):
        return f"d | {seqno} | ".encode() + data

def main():
    client = Client(Config())
    client.send_file()

if __name__ == '__main__':
    main()