"""
- pass an error thorugh grpc context: 
    https://stackoverflow.com/questions/40998199/raising-a-server-error-to-the-client-with-grpc

- logging:
    https://realpython.com/python-logging/

- use same logging in multiple modules
    https://stackoverflow.com/questions/15727420/using-logging-in-multiple-modules

- grpc google doc:
    https://developers.google.com/protocol-buffers/docs/reference/python-generated#map-fields

- grpc status codes
    https://grpc.github.io/grpc/python/grpc.html#grpc-status-code

- handle exception from grpc
    https://stackoverflow.com/questions/57306467/how-do-i-get-the-status-code-ok-response-from-a-grpc-client


"""


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

    # FIXME. UPD -> FIXED
    # There is a bug when two or more Nodes
    # have each other in their finger table
    # it could be that e.g. N13 tries to save key
    # on N28, but N28 lookup that it should be saved
    # on N13. So, it loops and stucks.

    # FIXME. UPD -> partially fixed (for removing)
    # If key will be saved on Node before others nodes
    # goes to chord, the new Node may not find this key.
    # Node should distribute its data keeper whenever 
    # new Nodes are connected or removed.

    # FIXME
    # If new node is connected
    # the data is not distributed over the chord 
    # to considering new finger tables.

    def __init__(self, ip: str, port: int, register_ip: str, register_port: int):
        self.ip = ip
        self.port = port
        self.register_ip = register_ip
        self.register_port = register_port
        self.finger_table: list[chord_pb2.NodeAddressAndId] = list()

        self._register_node()
        self.daemon = threading.Thread(target=self._refresh_finger_table, daemon=True)
        self.daemon.start()

        self.data_keeper: dict[str, str] = dict() # save data from client by key
    
    def GetFingerTable(self, request, context):
        table = {item.id: item.address for item in self.finger_table}
        return chord_pb2.GetFingerTableResponse(neighbours=table)

    def Save(self, request, context):
        target_id = self._compute_hash(request.key, self.m)
        log.info(f'Trying to save {request.key} key with hash {target_id}...')
        target_id = self._lookup(target_id)
        if target_id != self.id:
            # print('LOOKUP ID', target_id)
            address = next(filter(lambda x: x.id == target_id, self.finger_table)).address
            ipaddr, port = address.ip, address.port
            # log.info(;)
            channel = grpc.insecure_channel(
                f'{ipaddr}:{port}'
            )
            node_stub = chord_pb2_grpc.NodeServiceStub(channel)
            response = node_stub.Save(
                chord_pb2.SaveRequest(key=request.key, text=request.text)
            )
            
            if response.is_saved:
                log.info(f'Data has been saved on node id #{response.node_id}.')
            else:
                log.info('Data has not been saved!')
            return chord_pb2.SaveResponse(is_saved=response.is_saved, node_id=response.node_id)
        

        if request.key in self.data_keeper:
            log.info('The key is already exists!')
            # Return false, cause key already exists
            return chord_pb2.SaveResponse(is_saved=False, node_id=self.id)

        log.info(f'Data with key -> {request.key} has been saved on this node.')
        self.data_keeper[request.key] = request.text
        return chord_pb2.SaveResponse(is_saved=True, node_id=self.id)
    
    def Remove(self, request, context):
        target_id = self._compute_hash(request.key, self.m)
        log.info(f'Trying to remove {request.key} key with hash {target_id}...')
        target_id = self._lookup(target_id)
        if target_id != self.id:
            # print('LOOKUP ID', target_id)
            address = next(filter(lambda x: x.id == target_id, self.finger_table)).address
            ipaddr, port = address.ip, address.port
            # log.info(;)
            channel = grpc.insecure_channel(
                f'{ipaddr}:{port}'
            )
            node_stub = chord_pb2_grpc.NodeServiceStub(channel)
            response = node_stub.Remove(
                chord_pb2.RemoveRequest(key=request.key)
            )
            
            if response.is_saved:
                log.info(f'Data has been removed on node id #{response.node_id}.')
            else:
                log.info('Data has not been removed!')
            return chord_pb2.RemoveResponse(is_deleted=response.is_saved, node_id=response.node_id)

        if request.key not in self.data_keeper:
            log.info('Key has not been ever saved.')
            return chord_pb2.RemoveResponse(is_deleted=False)
        
        log.info(f'Key {request.key} has been removed.')
        del self.data_keeper[request.key]
        return chord_pb2.RemoveResponse(is_deleted=True, node_id=self.id)
    
    def Find(self, request, context):
        target_id = self._compute_hash(request.key, self.m)
        log.info(f'Trying to find {request.key} key with hash {target_id}...')
        target_id = self._lookup(target_id)
        log.info(f'Lookuped target: {target_id}!')
        if target_id != self.id:
            address = next(filter(lambda x: x.id == target_id, self.finger_table)).address
            ipaddr, port = address.ip, address.port
            channel = grpc.insecure_channel(
                f'{ipaddr}:{port}'
            )
            node_stub = chord_pb2_grpc.NodeServiceStub(channel)
            response = node_stub.Find(
                chord_pb2.FindRequest(key=request.key)
            )
            log.info(response)
            if response.is_found:
                log.info(f'The Key was found on {response.node_address.ip}:{response.node_address.port}')
                log.info(f'Text for the corresponding key is {response.text}.')
                return chord_pb2.FindResponse(
                    is_found=True,
                    node_id=response.node_id,
                    node_address=response.node_address,
                    text=response.text
                )
            else:
                log.info('Key was not found!')
                return chord_pb2.FindResponse(is_found=False)

        if request.key not in self.data_keeper:
            log.info('Key has never been saved.')
            return chord_pb2.FindResponse(is_found=False)
        
        log.info('Key was found on this node!')
        log.info(f'Text: {self.data_keeper[request.key]}')
        return chord_pb2.FindResponse(
            is_found=True, 
            node_id=self.id,
            node_address=chord_pb2.NodeAddress(ip=self.ip, port=self.port),
            text=self.data_keeper[request.key]
        )

    def GetServiceName(self, request, context):
        return chord_pb2.GetServiceNameResponse(
            service_name="node",
            node_id=self.id    
        )
    
    def Quit(self):
        # UPD. Fixed. distribute data keeper over the chord
        response = self.register_stub.DeregisterNode(
            chord_pb2.DeregisterNodeRequest(node_id=self.id)
        )

        if response.is_deregistered:
            log.info('Node has been deleted from the chord.')

        time.sleep(3)
        log.info('Transfering data keeper...')
        channel = grpc.insecure_channel(
                f'{self.pred_address.ip}:{self.pred_address.port}'
            )
        node_stub = chord_pb2_grpc.NodeServiceStub(channel)
        
        for k, v in self.data_keeper.items():
            response = node_stub.Save(
                chord_pb2.SaveRequest(key=k, text=v)
            )

        log.info('Shutting down...')
        exit(0)

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
        
        self.id = response.node_id # id of this Node in chord
        self.m = response.m # key size in this Chord

        log.info(f'Node has been started...{self.ip}:{self.port}')
        log.info(f'New Node it registered with id = {self.id}')


    def _refresh_finger_table(self):
        while True:
            request = {
                'node_id': self.id
            }
            response = self.register_stub.PopulateFingerTable(
                chord_pb2.PopulateFingerTableRequest(**request)
            )
            self.pred_id = response.pred_id
            self.pred_address = response.pred_address
            self.finger_table = list(response.neighbours)
            time.sleep(1)   # this is not true 1 second, 
                            # but that's enough for this task

    def _compute_hash(self, key, m) -> int:
        import zlib
        hash_value = zlib.adler32(key.encode())
        target_id = hash_value % 2 ** m

        return target_id

    def _lookup(self, key) -> int:
        """
        Lookup the target id over the chord.

        :param key: hash computed supposed id; could be ABSENT in the chord
        :param m: chord's key size in bits

        :return: target id
        """

        self.succ_id = self._find_successor()
        log.info(f'Lookup method: pred_id: {self.pred_id}, succ_id: {self.succ_id}')

        if self.pred_id < self.id:
            if self.pred_id < key <= self.id:
                log.info(f'1. Lookup up with id #{self.id}')
                return self.id
        elif key > self.pred_id or key <= self.id:
            log.info(f'2. Lookup up with id #{self.id}')
            return self.id

        log.info('Lookup method. Goes through cycle.')
        log.debug(f'{self.finger_table}')
        table = sorted([_.id for _ in self.finger_table])
        # idx = 0

        for i in range(len(table)):
            if table[(i + 1) % len(table)] > table[i]:
                if table[i] <= key < table[(i + 1) % len(table)]:
                    log.debug(f'3. Lookup up with id #{table[i]}')
                    return table[i]
            elif key >= table[i] or key < table[(i + 1) % len(table)]:
                log.debug(f'4. Lookup up with id #{table[i]}')
                return table[i]

        log.debug(f'5. Lookup up with id #{table[i]}')
        return self.succ_id
        # return table[0]
        

    def _find_successor(self):
        table = [_.id for _ in self.finger_table]
        for i in range(len(table)):
            if table[(i + 1) % len(table)] > table[i]:
                if table[i] <= self.id < table[(i + 1) % len(table)]:
                    return table[i]
            elif self.id >= table[i] or self.id < table[(i + 1) % len(table)]:
                return table[i]
        # if len(self.finger_table) == 0:
        #     return self.id
        # return self.finger_table[0].id

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
        handler.Quit()


if __name__ == "__main__":
    args = parser.parse_args()

    node_ip, node_port = args.node_address.split(':')
    reg_ip, reg_port = args.registry_address.split(':')

    try:
        run(NodeServiceHandler(node_ip, int(node_port), reg_ip, int(reg_port)))
    except Exception as e:
        log.debug(e)
