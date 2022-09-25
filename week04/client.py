import argparse

import grpc
import service_pb2
import service_pb2_grpc


parser = argparse.ArgumentParser()
parser.add_argument('address', help='Server address ip:port')


if __name__ == '__main__':
    address = parser.parse_args().address
    channel = grpc.insecure_channel(f'{address}')
    stub = service_pb2_grpc.UnicornServiceStub(channel)

    while True:
        try:
            print('> ', end='')
            cmd, *data = input().split(maxsplit=1)
            if cmd == 'reverse':
                msg = service_pb2.TextReq(data=data[0])
                response = stub.ReverseText(msg)
                print(response.data)
            elif cmd == 'split':
                msg = service_pb2.SplitTextReq(data=data[0], delim=' ')
                response = stub.SplitText(msg)
                print(response, end='')
            elif cmd == 'isprime':
                def func(numbers):
                    for num in numbers:
                        yield service_pb2.NumberReq(number=num)

                for entry in stub.IsPrime(func(map(int, data))):
                    print(entry.answer)
            elif cmd == 'exit':
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            print('Exit... Bye!')
            exit(0)
        except ValueError:
            print('Try again!')
