import grpc
import chord_pb2
import chord_pb2_grpc

import click

import logging
import logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger(__name__)


class ExitException(Exception):
    pass


class Client:

    def __init__(self):
        self.commands = {
            'connect': self.connect,
            'get_info': self.get_info,
            'quit': self.quit
        }
        self.stub = None

    def run_command(self, args: str):
        command, *params = args.split(maxsplit=1)
        if command not in self.commands:
            raise ValueError('Command not found!')
        
        self.commands[command](params)

    def connect(self, args):
        self.host, self.port = args[0].split(':')

        self.channel = grpc.insecure_channel(
            f'{self.host}:{self.port}'
        )

        # TODO different type of stubs
        # This part of code is peace of shit!!!
        # Many thanks to GRPC developers that
        # made a dumb documentation!
        # You, bastards!
        self.stub = chord_pb2_grpc.NodeServiceStub(self.channel)
        try:
            self.stub = chord_pb2_grpc.NodeServiceStub(self.channel)
            self.stub.GetServiceName(chord_pb2.GetServiceNameRequest())
        except Exception as e:
            log.error(f'{e}; Wrong service!')
        
        try:
            self.stub = chord_pb2_grpc.RegisterServiceStub(self.channel)
            self.stub.GetServiceName(chord_pb2.GetServiceNameRequest())
        except Exception as e:
            log.error(f'{e}; Wrong service!')
        
        
        empty = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        response = self.stub.GetServiceName(empty)
        print(f'Client connected to {response.service_name}: {self.host}:{self.port}')


    def get_info(self, *args):
        if self.stub is None:
            raise Exception('You have to connect either to node or register first!')
        if isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            request = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
            response = self.stub.GetFingerTable(request)
            log.info(str(response.neighbours))
        elif isinstance(self.stub, chord_pb2_grpc.RegisterServiceStub):
            request = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
            response = self.stub.GetChordInfo(request)
            log.info(str(response.nodes))

    def quit(self, *args):
        raise ExitException('Exit client...')


def main():
    client = Client()

    while True:
        try:
            cmd = click.prompt('', type=str, prompt_suffix='>')
            client.run_command(cmd)
        except click.exceptions.Abort as e:
            log.debug(e)
            exit(0)
        except ExitException as e:
            log.info(e)
            exit(0)
        except Exception as e:
            log.exception(e)


if __name__ == '__main__':
    main()