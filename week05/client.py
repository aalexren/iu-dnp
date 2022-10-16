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
        print(self.host, self.port)

        self.channel = grpc.insecure_channel(
            f'{self.host}:{self.port}'
        )

        # XXX different type of stubs
        # This part of code is peace of shit!!!
        # Many thanks to GRPC developers that
        # made a dumb documentation!
        # You, bastards!

        stubs = [
            chord_pb2_grpc.NodeServiceStub(self.channel),
            chord_pb2_grpc.RegisterServiceStub(self.channel)
        ]
        empty = chord_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        response = None

        for stub in stubs:
            try:
                response = stub.GetServiceName(empty)
                self.stub = stub
                break
            except grpc.RpcError as e:
                """
                issue: https://shorturl.at/gikov
                """
                # log.debug(f'{e.code()}; Wrong service!')
                continue

        print(f'Client connected to {response.service_name}: {self.host}:{self.port}')
        # TODO
        if response.node_id:
            print(f'Node id #{response.node_id}')


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
            print(f'{k}\t-> {v.ip}:{v.port}')


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
        response = self.stub.Save(
            chord_pb2.SaveRequest(**request)
        )
        if response.is_saved:
            print(f"{key} has been saved on Node with id #{response.node_id}")
        else:
            print(f"Key was not saved.")


    def remove(self, args):
        """Node applied method only.
        """

        if not isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            raise Exception('You have to connect to node first!')
        
        key = args[0]
        request = {
            'key': key
        }

        response = self.stub.Remove(
            chord_pb2.RemoveRequest(**request)
        )
        if response.is_deleted:
            print(f"{key} has been removed from Node with id #{response.node_id}")
        else:
            print(f"Key was not removed.")


    def find(self, args):
        """Node applied method only.
        """

        if not isinstance(self.stub, chord_pb2_grpc.NodeServiceStub):
            raise Exception('You have to connect to node first!')
        
        key = args[0]
        request = {
            'key': key
        }

        response = self.stub.Find(
            chord_pb2.FindRequest(**request)
        )
        if response.is_found:
            print(f"{key} has been found on Node with id #{response.node_id} \
                with {response.node_address.ip}:{response.node_address.port}")
            print(f'Text: {response.text}')
        else:
            print(f"Key was not found.")


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