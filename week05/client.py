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
            'save': self.save,
            'remove': self.remove,
            'find': self.find,
            'quit': self.quit
        }
        self.stub = None

    def run_command(self, args: str):
        command, *params = args.split(maxsplit=1)
        if command not in self.commands:
            raise ValueError('Command not found!')
        
        self.commands[command](params)

    def connect(self, args):
        """Node and Register applied method.
        """

        self.host, self.port = args[0].split(':')

        self.channel = grpc.insecure_channel(
            f'{self.host}:{self.port}'
        )

        # XXX different type of stubs
        # This part of code is peace of shit!!!
        # Many thanks to GRPC developers that
        # made a dumb documentation!
        # You, bastards!
        self.stub = chord_pb2_grpc.NodeServiceStub(self.channel)
        try:
            self.stub = chord_pb2_grpc.NodeServiceStub(self.channel)
            self.stub.GetServiceName(chord_pb2.GetServiceNameRequest())
        except Exception as e:
            pass
            # log.warning(f'{e}; Wrong service!')
        
        try:
            self.stub = chord_pb2_grpc.RegisterServiceStub(self.channel)
            self.stub.GetServiceName(chord_pb2.GetServiceNameRequest())
        except Exception as e:
            pass
            # log.warning(f'{e}; Wrong service!')
        
        
        empty = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        response = self.stub.GetServiceName(empty)
        print(f'Client connected to {response.service_name}: {self.host}:{self.port}')


    def get_info(self, *args):
        """Node and Register applied method.
        """

        if self.stub is None:
            raise Exception('You have to connect either to node or register first!')
        if isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            request = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
            response = self.stub.GetFingerTable(request)
            response = response.neighbours
        elif isinstance(self.stub, chord_pb2_grpc.RegisterServiceStub):
            request = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
            response = self.stub.GetChordInfo(request)
            response = response.nodes

        for k, v in response.items():
            print(f'id={k} -> {v.ip}:{v.port}')

    def save(self, args):
        """Node applied method only.
        """

        if not isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            raise Exception('You have to connect to node first!')

        key, text = args[0].split('" ', maxsplit=1)
        key = key[1:]

        request = {
            'key': key,
            'text': text
        }
        response = self.stub.SaveRequest(**request)
        if response.is_saved:
            print(f"{key} has been saved on Node with id #{response.node_id}")
        else:
            print(f"{response.details}")

    def remove(self, args):
        """Node applied method only.
        """

        if not isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            raise Exception('You have to connect to node first!')
        
        key = args[0]
        request = {
            'key': key
        }

        response = self.stub.RemoveRequest(**request)
        if response.is_deleted:
            print(f"{key} has been saved on Node with id #{response.node_id}")
        else:
            print(f"{response.details}")


    def find(self, args):
        """Node applied method only.
        """

        if not isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            raise Exception('You have to connect to node first!')
        
        key = args[0]
        request = {
            'key': key
        }

        response = self.stub.FindRequest(**request)
        if response.is_found:
            print(f"{key} has been saved on Node with id #{response.node_id} \
                with {response.node_address.ip}:{response.node_address.port}")
        else:
            print(f"{response.details}")

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
            log.info(e)


if __name__ == '__main__':
    main()