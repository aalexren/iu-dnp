from app.support import chord_pb2_grpc
from app.support import chord_pb2

import logging
log = logging.getLogger(__name__)

class Register(chord_pb2_grpc.RegisterServiceServicer):
    
    def RegisterNode(self, request, context):
        return super().RegisterNode(request, context)

    def DeregisterNode(self, request, context):
        return super().DeregisterNode(request, context)

    def PopulateFingerTable(self, request, context):
        return super().PopulateFingerTable(request, context)
    
    def GetChordInfo(self, request, context):
        return super().GetChordInfo(request, context)