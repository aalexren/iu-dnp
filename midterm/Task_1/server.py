import grpc
import queue_pb2 as queue
import queue_pb2_grpc as queue_grpc

from concurrent import futures
import sys

PORT = int(sys.argv[1])
QSIZE = int(sys.argv[2])

class QueueServiceHandler(queue_grpc.QueueServiceServicer):
    def __init__(self, qsize: int):
        self.queue: list[str] = []
        self.qsize = qsize

    def put(self, request, context):
        is_put = False
        
        if len(self.queue) < self.qsize:
            self.queue.append(request.item)
            is_put = True
        
        response = {
            'is_put': is_put
        }
        return queue.PutResponse(**response)
        

    def peek(self, request, context):
        ret = None

        if len(self.queue):
            ret = self.queue[0]

        response = {
            'item': ret
        }

        return queue.PeekResponse(**response)

    def pop(self, request, context):
        ret = None

        if len(self.queue):
            self.queue.reverse()
            ret = self.queue.pop()
            self.queue.reverse()
        
        response = {
            'item': ret
        }

        return queue.PopResponse(**response)

    def size(self, request, context):
        response = {
            'size': len(self.queue)
        }

        return queue.SizeResponse(**response)

def run(handler: QueueServiceHandler):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    queue_grpc.add_QueueServiceServicer_to_server(
        handler, server
    )
    server.add_insecure_port(f'[::]:{PORT}')
    server.start()
    try:
        print('Server started...')
        server.wait_for_termination()
    except KeyboardInterrupt:
        print.info('Shutting down...')

if __name__ == '__main__':
    run(QueueServiceHandler(QSIZE))