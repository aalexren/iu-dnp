import random as rnd
rnd.seed(0)

from concurrent import futures
import argparse

import grpc
import chord_pb2_grpc
import chord_pb2

import logging
import logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('address', help='<ip>:<port>', type=str)
parser.add_argument('m', help='key size in bits', type=int)


class RegisterServiceHandler(chord_pb2_grpc.RegisterServiceServicer):
    
    def __init__(self, ip: str, port: int, m: int):
        self.ip = ip
        self.port = port
        self.key_size = m # in bits
        self.chord_nodes: dict[int, chord_pb2.NodeAddress]  = dict() # list of registered nodes
        self.chord_nodes_list = [-1 for i in range(0, 2 ** m)]

        # XXX
        # self.chord_nodes[5] = chord_pb2.NodeAddress(ip='127.0.0.1', port=5678)
        # self.chord_nodes_list[5] = 5

        super().__init__()


    def RegisterNode(self, request, context):
        
        new_node_ip = request.address.ip
        new_node_port = request.address.port
        for address in self.chord_nodes.values():
            if new_node_ip == address.ip and new_node_port == address.port:
                context.set_code(grpc.StatusCode.RESOURSE_EXHAUSTED)
                context.set_details("Address is already in use!")
                return chord_pb2.RegisterNodeResponse()

        try:
            new_id = self._get_free_id()
        except Exception as e:
            log.exception(e)
            context.set_code(grpc.StatusCode.RESOURSE_EXHAUSTED)
            context.set_details("Chord is full!")
            return chord_pb2.RegisterNodeResponse()


        self.chord_nodes[new_id] = chord_pb2.NodeAddress(
            ip=request.address.ip, port=request.address.port
        )
        self.chord_nodes_list[new_id] = new_id
        log.info(f'New node if registered with id {new_id}.')

        response = {
            'node_id': new_id,
            'm': self.key_size
        }
        return chord_pb2.RegisterNodeResponse(**response)


    def DeregisterNode(self, request, context):
        del_id = request.node_id
        if del_id in self.chord_nodes:
            del self.chord_nodes[del_id]
            self.chord_nodes_list[del_id] = -1
            log.info(f'Node with id {del_id} has been deregistered.')
            response = {
                'is_deregistered': True
            }
            return chord_pb2.DeregisterNodeResponse(**response)
        
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Node was not found!")
        return chord_pb2.DeregisterNodeResponse()


    def PopulateFingerTable(self, request, context):
        node_id = request.node_id

        fingers = self._get_finger_table(node_id)
        # finger self.chord_nodes[finger] for finger in fingers]
        finger_table = [
            chord_pb2.NodeAddressAndId(
                id=finger,
                address=self.chord_nodes[finger]
            )
            for finger in fingers
        ]

        predecessor = self._closest_preceding_node(node_id)
        pred_address = self.chord_nodes[predecessor]

        response = {
            'pred_id': predecessor,
            'pred_address': chord_pb2.NodeAddress(ip=pred_address.ip, port=pred_address.port),
            'neighbours': finger_table
        }

        return chord_pb2.PopulateFingerTableResponse(**response)
    

    def GetChordInfo(self, request, context):
        response = {
            'nodes': self.chord_nodes
        }
        return chord_pb2.GetChordInfoResponse(**response)

    def GetServiceName(self, request, context):
        # print(f'{context.code()}, {context.details()}')
        return chord_pb2.GetServiceNameResponse(service_name="register")
    

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
    
    def _find_successor(self, node_id: int) -> int:
        """Find first available successor in the chord.

        N + 1 -> N11, but N11 is not the part of the chord, so
        next available is N14, hence successor is N14.
        """
        for i in range(node_id + 1, len(self.chord_nodes_list)):
            if self.chord_nodes_list[i] != -1:
                return i
        
        for i in range(0, node_id + 1):
            if self.chord_nodes_list[i] != -1:
                return i

    def _closest_preceding_node(self, node_id: int) -> int:
        """Find first available predecessor in the chord
        counter clockwise, starting from node_id - 1.
        """
        for i in range(node_id - 1, 0 - 1, -1):
            if self.chord_nodes_list[i] != -1:
                return self.chord_nodes_list[i]
        
        for i in range(2 ** self.key_size - 1, node_id - 1, -1):
            if self.chord_nodes_list[i] != -1:
                return self.chord_nodes_list[i]
        

    def _build_raw_finger_table(self, node_id) -> list[int]:
        """Calculate finger table with supposing steps of neighbours.

        N + 1 -> N11
        N + 2 -> N12
        N + 4 -> N14
        N + 8 -> N18
        etc.
        """
        unique = set()
        res: list[int] = []
        for i in range(1, self.key_size + 1):
            successor = (node_id + 2 ** (i - 1)) % (2 ** self.key_size)
            if successor not in unique:
                res.append(successor)
            unique.add(successor)
        return res
    
    def _get_finger_table(self, node_id) -> list[int]:
        """Calculate true finger table

        N + 1 -> N14
        N + 2 -> N14
        N + 4 -> N14
        N + 8 -> N29
        etc.
        """
        raw_finger_table = self._build_raw_finger_table(node_id)
        finger_table = []
        for i, v in enumerate(raw_finger_table):
            if v in self.chord_nodes:
                finger_table.append(v)
            elif self._find_successor(v) != node_id:
                finger_table.append(self._find_successor(v))
        
        return finger_table


def run(handler: RegisterServiceHandler):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chord_pb2_grpc.add_RegisterServiceServicer_to_server(
        handler, server
    )
    server.add_insecure_port(f'[::]:{handler.port}')
    server.start()
    try:
        log.info(f'Server has been started...{handler.ip}:{handler.port}')
        server.wait_for_termination()
    except KeyboardInterrupt:
        log.info('Shutting down...')


if __name__ == "__main__":
    args = parser.parse_args()
    ip, port = args.address.split(':')
    m = args.m
    
    run(RegisterServiceHandler(ip, int(port), m))
