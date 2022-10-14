from app.support import chord_pb2_grpc
from app.support import chord_pb2


import logging
log = logging.getLogger(__name__)


class Node(chord_pb2_grpc.NodeServiceServicer):
    
    def GetFingerTable(self, request, context):
        return super().GetFingerTable(request, context)

    def Save(self, request, context):
        return super().Save(request, context)
    
    def Remove(self, request, context):
        return super().Remove(request, context)
    
    def Find(self, request, context):
        return super().Find(request, context)