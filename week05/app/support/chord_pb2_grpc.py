# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import chord_pb2 as chord__pb2


class HashTableServiceStub(object):
    """Methods for the Register, Node and Client entities.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RegisterNode = channel.unary_unary(
                '/HashTableService/RegisterNode',
                request_serializer=chord__pb2.RegisterNodeRequest.SerializeToString,
                response_deserializer=chord__pb2.RegisterNodeResponse.FromString,
                )
        self.DeregisterNode = channel.unary_unary(
                '/HashTableService/DeregisterNode',
                request_serializer=chord__pb2.DeregisterNodeRequest.SerializeToString,
                response_deserializer=chord__pb2.DeregisterNodeResponse.FromString,
                )
        self.PopulateFingerTable = channel.unary_unary(
                '/HashTableService/PopulateFingerTable',
                request_serializer=chord__pb2.PopulateFingerTableRequest.SerializeToString,
                response_deserializer=chord__pb2.PopulateFingerTableResponse.FromString,
                )
        self.GetChordInfo = channel.unary_unary(
                '/HashTableService/GetChordInfo',
                request_serializer=chord__pb2.ChordRingInfoRequest.SerializeToString,
                response_deserializer=chord__pb2.ChordRingInfoResponse.FromString,
                )
        self.GetFingerTable = channel.unary_unary(
                '/HashTableService/GetFingerTable',
                request_serializer=chord__pb2.GetFingerTableRequest.SerializeToString,
                response_deserializer=chord__pb2.GetFingerTableResponse.FromString,
                )
        self.Save = channel.unary_unary(
                '/HashTableService/Save',
                request_serializer=chord__pb2.SaveRequest.SerializeToString,
                response_deserializer=chord__pb2.SaveResponse.FromString,
                )
        self.Remove = channel.unary_unary(
                '/HashTableService/Remove',
                request_serializer=chord__pb2.RemoveRequest.SerializeToString,
                response_deserializer=chord__pb2.RemoveResponse.FromString,
                )
        self.Find = channel.unary_unary(
                '/HashTableService/Find',
                request_serializer=chord__pb2.FindRequest.SerializeToString,
                response_deserializer=chord__pb2.FindResponse.FromString,
                )


class HashTableServiceServicer(object):
    """Methods for the Register, Node and Client entities.
    """

    def RegisterNode(self, request, context):
        """Invoked by Node to Register itself with given ip address 
        and port. Returns registered id and m, where 
        m - size of key for chord ring.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeregisterNode(self, request, context):
        """Register drop Node out of the chord ring.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PopulateFingerTable(self, request, context):
        """Share list of all neighbours and predecessor
        to node with given id.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetChordInfo(self, request, context):
        """Share to Client list of all existing nodes in the chord ring.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetFingerTable(self, request, context):
        """Client call Node to get finger table of this Node.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Save(self, request, context):
        """Client (or Node) call Node to save text on some Node,
        which id (target Node id) will be evaluated using key
        on called Node using lookup.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Remove(self, request, context):
        """Client (or Node) call Node to remove key and corresponding text,
        which id (target Node id) will be evaluated using key 
        on called Node using lookup.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Find(self, request, context):
        """Client (or Node) call Node to find text by given key,
        which id (target Node id) will be evaluated using key 
        on called Node using lookup.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_HashTableServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RegisterNode': grpc.unary_unary_rpc_method_handler(
                    servicer.RegisterNode,
                    request_deserializer=chord__pb2.RegisterNodeRequest.FromString,
                    response_serializer=chord__pb2.RegisterNodeResponse.SerializeToString,
            ),
            'DeregisterNode': grpc.unary_unary_rpc_method_handler(
                    servicer.DeregisterNode,
                    request_deserializer=chord__pb2.DeregisterNodeRequest.FromString,
                    response_serializer=chord__pb2.DeregisterNodeResponse.SerializeToString,
            ),
            'PopulateFingerTable': grpc.unary_unary_rpc_method_handler(
                    servicer.PopulateFingerTable,
                    request_deserializer=chord__pb2.PopulateFingerTableRequest.FromString,
                    response_serializer=chord__pb2.PopulateFingerTableResponse.SerializeToString,
            ),
            'GetChordInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.GetChordInfo,
                    request_deserializer=chord__pb2.ChordRingInfoRequest.FromString,
                    response_serializer=chord__pb2.ChordRingInfoResponse.SerializeToString,
            ),
            'GetFingerTable': grpc.unary_unary_rpc_method_handler(
                    servicer.GetFingerTable,
                    request_deserializer=chord__pb2.GetFingerTableRequest.FromString,
                    response_serializer=chord__pb2.GetFingerTableResponse.SerializeToString,
            ),
            'Save': grpc.unary_unary_rpc_method_handler(
                    servicer.Save,
                    request_deserializer=chord__pb2.SaveRequest.FromString,
                    response_serializer=chord__pb2.SaveResponse.SerializeToString,
            ),
            'Remove': grpc.unary_unary_rpc_method_handler(
                    servicer.Remove,
                    request_deserializer=chord__pb2.RemoveRequest.FromString,
                    response_serializer=chord__pb2.RemoveResponse.SerializeToString,
            ),
            'Find': grpc.unary_unary_rpc_method_handler(
                    servicer.Find,
                    request_deserializer=chord__pb2.FindRequest.FromString,
                    response_serializer=chord__pb2.FindResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'HashTableService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class HashTableService(object):
    """Methods for the Register, Node and Client entities.
    """

    @staticmethod
    def RegisterNode(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/RegisterNode',
            chord__pb2.RegisterNodeRequest.SerializeToString,
            chord__pb2.RegisterNodeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeregisterNode(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/DeregisterNode',
            chord__pb2.DeregisterNodeRequest.SerializeToString,
            chord__pb2.DeregisterNodeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PopulateFingerTable(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/PopulateFingerTable',
            chord__pb2.PopulateFingerTableRequest.SerializeToString,
            chord__pb2.PopulateFingerTableResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetChordInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/GetChordInfo',
            chord__pb2.ChordRingInfoRequest.SerializeToString,
            chord__pb2.ChordRingInfoResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetFingerTable(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/GetFingerTable',
            chord__pb2.GetFingerTableRequest.SerializeToString,
            chord__pb2.GetFingerTableResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Save(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/Save',
            chord__pb2.SaveRequest.SerializeToString,
            chord__pb2.SaveResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Remove(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/Remove',
            chord__pb2.RemoveRequest.SerializeToString,
            chord__pb2.RemoveResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Find(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/HashTableService/Find',
            chord__pb2.FindRequest.SerializeToString,
            chord__pb2.FindResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
