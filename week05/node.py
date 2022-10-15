from concurrent import futures
import argparse
import threading
import time

import chord_pb2_grpc
import chord_pb2
import grpc

import logging
import logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('node_address', help='<ip>:<port>', type=str)
parser.add_argument('registry_address', help='<ip>:<port>', type=str)


class NodeServiceHandler(chord_pb2_grpc.NodeServiceServicer):
    def __init__(self, ip: str, port: int, register_ip: str, register_port: int):
        self.ip = ip
        self.port = port
        self.register_ip = register_ip
        self.register_port = register_port
        self.finger_table: dict[int, chord_pb2.NodeAddress] = dict()

        self._register_node()
        self.daemon = threading.Thread(target=self._refresh_finger_table, daemon=True)
        self.daemon.start()
    
    def GetFingerTable(self, request, context):
        return super().GetFingerTable(request, context)

    def Save(self, request, context):
        return super().Save(request, context)
    
    def Remove(self, request, context):
        return super().Remove(request, context)
    
    def Find(self, request, context):
        return super().Find(request, context)

    def GetServiceName(self, request, context):
        return chord_pb2.GetServiceNameResponse(service_name="node")

    def _register_node(self):
        channel = grpc.insecure_channel(
            f'{self.register_ip}:{self.register_port}'
        )
        self.register_stub = chord_pb2_grpc.RegisterServiceStub(channel)

        request = {
            'address': chord_pb2.NodeAddress(ip=self.ip, port=self.port)
        }

        try:
            response = self.register_stub.RegisterNode(
                chord_pb2.RegisterNodeRequest(**request)
            )
        except Exception as e:
            log.info(e)
            exit(128)
        
        self.node_id = response.node_id # id of this Node in chord
        self.m = response.m # key size in this Chord

        log.info(f'Node has been started...{self.ip}:{self.port}')
        log.info(f'New Node it registered with id = {self.node_id}')


    def _refresh_finger_table(self):
        while True:
            request = {
                'node_id': self.node_id
            }
            response = self.register_stub.PopulateFingerTable(
                chord_pb2.PopulateFingerTableRequest(**request)
            )
            print(response)
            time.sleep(1)


def run(handler: NodeServiceHandler):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chord_pb2_grpc.add_NodeServiceServicer_to_server(
        handler, server
    )
    server.add_insecure_port(f'[::]:{handler.port}')
    try:
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        log.info('Shutting down...')


if __name__ == "__main__":
    args = parser.parse_args()

    node_ip, node_port = args.node_address.split(':')
    reg_ip, reg_port = args.registry_address.split(':')

    try:
        run(NodeServiceHandler(node_ip, int(node_port), reg_ip, int(reg_port)))
    except Exception as e:
        log.debug(e)
