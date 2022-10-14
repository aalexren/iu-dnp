from . import chord_pb2_grpc
from . import chord_pb2


import logging
log = logging.getLogger(__name__)


class NodeAddress:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

class NodeServiceHandler(chord_pb2_grpc.NodeServiceServicer):
    
    def GetFingerTable(self, request, context):
        return super().GetFingerTable(request, context)

    def Save(self, request, context):
        return super().Save(request, context)
    
    def Remove(self, request, context):
        return super().Remove(request, context)
    
    def Find(self, request, context):
        return super().Find(request, context)