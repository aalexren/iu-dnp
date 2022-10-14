import random as rnd
from concurrent import futures

import chord_pb2_grpc
import chord_pb2

from .node import NodeAddress

import grpc

import logging
log = logging.getLogger(__name__)


class RegisterServiceHandler(chord_pb2_grpc.RegisterServiceServicer):
    
    def __init__(self, ip: str, port: int, m: int):
        self.ip = ip
        self.port = port
        self.key_size = m # in bits
        self.chord_nodes: dict[int, NodeAddress]  = dict() # list of registered nodes
        super().__init__()

    def RegisterNode(self, request, context):
        
        try:
            new_id = self._get_free_id()
        except Exception as e:
            log.exception(e)
            context.set_code(grpc.StatusCode.RESOURSE_EXHAUSTED)
            context.set_details("Chord is full!")
            return chord_pb2.RegisterNodeResponse()
        
        self.chord_nodes[new_id] = NodeAddress(request.address.ip, request.address.port)

        response = {
            'node_id': new_id,
            'm': self.key_size
        }
        return chord_pb2.RegisterNodeResponse(**response)

    def DeregisterNode(self, request, context):
        del_id = request.node_id
        if del_id in self.chord_nodes:
            del self.chord_nodes[del_id]
            response = {
                'is_deregistered': True
            }
            return chord_pb2.DeregisteredNodeResponse(**response)
        
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Node was not found!")
        return chord_pb2.DeregisteredNodeResponse()

    def PopulateFingerTable(self, request, context):
        node_id = request.node_id


        return super().PopulateFingerTable(request, context)
    
    def GetChordInfo(self, request, context):
        response = {
            'neighbours': self.chord_nodes
        }
        return chord_pb2.GetChordInfoResponse(**response)

    def run(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chord_pb2_grpc.add_RegisterServiceServicer_to_server(
            RegisterServiceHandler(), server
        )
        server.add_insecure_port(f'[::]:{self.port}')
        server.start()
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            print('Shutting down...')

    
    def _get_free_id(self) -> int:
        """Generate available id for new node.

        Raises exception if chord is full.
        """

        if len(self.chord_nodes) >= 2 ** self.key_size:
            raise LookupError("No available id!")

        new_id = rnd.randint(0, 2 ** self.key_size - 1)
        while new_id in self.chord_nodes:
            new_id = rnd.randint(0, 2 ** self.key_size - 1)
        
        return new_id


if __name__ == "__main__":
    RegisterServiceHandler("127.0.0.1", 5555, 5).run()
