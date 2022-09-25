"""
To generate protobuf classes for gRPC use this command:

"""


from concurrent import futures
import argparse
import logging

import grpc
import service_pb2
import service_pb2_grpc


parser = argparse.ArgumentParser()
parser.add_argument('port', help='Server port', type=int)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UnicornServiceHandler(service_pb2_grpc.UnicornServiceServicer):
    def ReverseText(self, request, context):
        reverse = request.data[::-1]
        return service_pb2.TextRep(data=reverse)
    

    def SplitText(self, request, context):
        data = request.data
        delim = request.delim
        res = data.split(delim)
        return service_pb2.SplitTextRep(count=len(res), chunk=res)
    

    def IsPrime(self, request_iterator, context):
        for req in request_iterator:
            res = self._is_prime(req.number)
            yield service_pb2.NumberRep(answer=f"{req.number} is{(not res)*' not'} prime")

    
    def _is_prime(self, number) -> bool:
        if number < 2: return False
        for i in range(2, int(number**0.5 + 1), 1):
            if number % i == 0 and i != number:
                return False
        return True


def serve():
    port = parser.parse_args().port

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_UnicornServiceServicer_to_server(
        UnicornServiceHandler(),server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print('Shutting down...')


if __name__ == '__main__':
    logging.basicConfig()
    serve()