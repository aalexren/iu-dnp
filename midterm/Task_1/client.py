from urllib import request
import grpc
import queue_pb2 as queue
import queue_pb2_grpc as queue_grpc

import sys

HOST, PORT = sys.argv[1].split(':')

def main():
    channel = grpc.insecure_channel(f"{HOST}:{PORT}")
    stub = queue_grpc.QueueServiceStub(channel)

    empty = queue.google_dot_protobuf_dot_empty__pb2.Empty()

    while True:
        try:
            cmd, *param = input("> ").split()
            if cmd == 'put':
                item = param[0]
                request = {
                    'item': item
                }
                response = stub.put(
                    queue.PutRequest(**request)
                )
                print(response.is_put)
            elif cmd == 'peek':
                response = stub.peek(empty)
                if response.item:
                    print(response.item)
            elif cmd == 'size':
                response = stub.size(empty)
                print(response.size)
            elif cmd == 'pop':
                response = stub.pop(empty) # залил версию без параметра empty
                if response.item:
                    print(response.item)
                else:
                    print(response.item)
        except KeyboardInterrupt:
            exit()

if __name__ == "__main__":
    main()