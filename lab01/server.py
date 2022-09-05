import os
import argparse
import socket
import select
from datetime import datetime

class Config:
    def __init__(self):
        self._config = {}
        self._set_cli_args()
    
    @property
    def port(self):
        return self._port

    def _set_cli_args(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('port', nargs='+', help='socket port')
        args = self.parser.parse_args()

        self._port = int(args.port[0])

    def __repr__(self):
        return f'{self._port}'


class Client:
    def __init__(self, address: tuple, filename: str, expected_size: int, seqno: int):
        self._address = address
        self._filename = filename
        self._expected_size = expected_size
        self._seqno: int = seqno
        self._last_access = datetime.now()
        self._data = []

    @property
    def last_access(self):
        self._last_access = datetime.now()
        return self._last_access
    
    @property
    def expected_size(self):
        return self._expected_size

    @property
    def filename(self):
        return self._filename

    @property
    def seqno(self) -> int:
        return self._seqno
    
    @seqno.setter
    def seqno(self, n_seqno):
        self._seqno = n_seqno

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, chunk):
        self._data.append(chunk)

    def __repr__(self):
        return f"{self._address} {self._filename} {self._expected_size} {self._seqno} {self.last_access}"


class Server:
    def __init__(self, config: Config):
        self.config = config
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.config.port,))
        print(self.socket.getsockname())
        self.clients: dict = {}
        self.buf_size = 1024
    
    def start_loop(self):
        while True:
            packet = self.socket.recvfrom(self.buf_size)
            address = packet[1]
            self._parse_packet(packet)
            if len(b''.join(self.clients[address].data)) >= self.clients[address].expected_size:
                self._save_file(address)
    
    def _save_file(self, address):
        with open(self.clients[address].filename, 'wb') as f:
            for chunk in self.clients[address].data:
                f.write(chunk)
        print('File has been saved successfully!')

    def _parse_packet(self, packet: bytes):
        data = packet[0].split(' | '.encode())
        address = packet[1]
        if data[0].startswith(b's'):
            print(f'Got new start message from {address}')
            prefix, seqno, filename, total_size = map(bytes.decode, data)
            self.clients[address] = Client(address, filename, int(total_size), int(seqno))
            self._send_start_ack(address)
        elif data[0].startswith(b'd'):
            self.clients[address].last_access
            prefix, seqno, data_bytes = data
            seqno = int(seqno.decode())
            print(f'Got new data message from {address} with seqno {seqno}')
            if seqno == self.clients[address].seqno + 1:
                self.clients[address].data = data_bytes
                self.clients[address].seqno = seqno
            self._send_data_ack(address)
            
    def _send_start_ack(self, address):
        packet = self.__format_start_ack_packet(self.clients[address].seqno + 1)
        self.socket.sendto(packet, address)
    
    def _send_data_ack(self, address):
        packet = self.__format_data_ack_packet(self.clients[address].seqno + 1)
        self.socket.sendto(packet, address)

    def __format_start_ack_packet(self, n_seqno: int):
        return f"a | {n_seqno} | {self.buf_size}".encode()

    def __format_data_ack_packet(self, n_seqno: int):
        return f"a | {n_seqno}".encode()


def main():
    server = Server(Config())
    server.start_loop()

if __name__ == '__main__':
    main()