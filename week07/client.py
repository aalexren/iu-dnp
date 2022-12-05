import grpc
import raft_pb2
import raft_pb2_grpc

class Address:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def __repr__(self):
        return f"<{self.ip}:{self.port}>"

class User:
    def __init__(self):
        self.address = None
        self.channel = None
        self.stub = None

    def connect(self, ip: str, port: str):
        self.address = Address(ip, int(port))
        self.channel = grpc.insecure_channel(
            f'{ip}:{int(port)}'
        )
        self.stub = raft_pb2_grpc.RaftServiceStub(self.channel)

    def get_leader(self) -> str:
        if not self.address:
            raise KeyError('Specify the target address!')
        request = {}
        try:
            response = self.stub.GetLeader(
                raft_pb2.GetLeaderRequest(**request)
            )

            return f"{response.leaderId} {response.address}"
        except grpc.RpcError:
            raise grpc.RpcError('Server is unavailable!')

    def suspend(self, period: float):
        if not self.address:
            raise KeyError('Specify the target address!')
        request = {
            'period': float(period)
        }
        try:
            response = self.stub.Suspend(
                raft_pb2.SuspendRequest(**request)
            )
        except grpc.RpcError:
            raise grpc.RpcError('Server is unavailable!')
            
    def set_val(self, key, value):
        if not self.address:
            raise KeyError('Specify the target address!')
        request = {
            'key': key,
            'value': value
        }
        try:
            response = self.stub.SetVal(
                raft_pb2.SetValRequest(**request)
            )
        except grpc.RpcError:
            raise grpc.RpcError('Server is unavailable!')

    def get_val(self, key) -> str:
        if not self.address:
            raise KeyError('Specify the target address!')
        request = {
            'key': key
        }
        try:
            response = self.stub.GetVal(
                raft_pb2.SetValRequest(**request)
            )
            return f"{response.value}"
        except grpc.RpcError:
            raise grpc.RpcError('Server is unavailable!')

    def quit(self):
        raise KeyboardInterrupt

class UserManager:
    def __init__(self):
        self.manager = User()
        self.build()

    def run(self):
        print('The client starts')
        while True:
            try:
                cmd, *args = input('> ').split()
                self.execute(cmd, args)
            except KeyboardInterrupt:
                print('The client ends')
                exit()
            except grpc.RpcError as e:
                print(f'{e}')
            except KeyError as e:
                print(f'{e}')
            except TypeError as e:
                print(f'{e}')
    
    def execute(self, cmd, *args):
        if not cmd in self.commands:
            raise KeyError('Not a command!')
        response = self.commands[cmd](*args[0])
        if response:
            print(response)

    def build(self):
        self.commands = {
            'connect': self.manager.connect,
            'getleader': self.manager.get_leader,
            'suspend': self.manager.suspend,
            'setval': self.manager.set_val,
            'getval': self.manager.get_val,
            'quit': self.manager.quit
        }

def main():
    manager = UserManager()
    manager.run()

if __name__ == '__main__':
    main()