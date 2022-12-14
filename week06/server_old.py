import grpc
import raft_pb2_grpc as raft_grpc
import raft_pb2 as raft

import threading
import time
import sys
import random as rnd

from typing import Union
from enum import Enum
from concurrent import futures
# from queue import Queue

INTERVAL = 0.001

class State(Enum):
    Follower = 1,
    Candidate = 2,
    Leader = 3


class Status(Enum):
    Suspended = 1,
    Running = 2


class Server(raft_grpc.RaftServiceServicer):
    def __init__(self, id: int, address: str, neighbours):
        """
        Makes a Server instance.

        :param id: id of the server
        :param address: address in form of <ip:port>
        :param neighbours: list of (id, address) tuples
        """
        super().__init__()
        self.id = id
        self.address = address
        self.neighbours = neighbours
        # self.queue = Queue(len(neighbours))
        self.state = State.Follower
        self.term = 0
        
        self.reset_time = rnd.randint(150, 300) # ms
        print(f'I am a {self.state}. Term: {self.term}. Reset time = {self.reset_time}')
        self.counter = 0 # timer counter
        self.leader: Union[tuple, None] = None # (id, address) of leader
        self.isVoted = False
        self.status = Status.Running
        # self.timer = self.__start_timer().start()
        self.__start_timer().start()
    
    def RequestVote(self, request, context):
        candidate_term = request.candidateTerm
        candidate_id = request.candidateId
        result = False

        if candidate_term == self.term and not self.isVoted:
            self.isVoted = True
            result = True
        if candidate_term > self.term:
            self.term = candidate_term
            self.isVoted = True
            result = True
        
        self.counter = 0 # you will always reset the timer
        if self.state == State.Candidate or self.state == State.Leader and result:
            self.term += 1
            self.isVoted = False
            self.state = State.Follower

        response = {
            'term': self.term,
            'result': result
        }
        return raft.RequestVoteResponse(**response)

    def AppendEntries(self, request, context):
        term = request.leaderTerm
        leader_id = request.leaderId
        success = True if term >= self.term else False
        self.counter = 0
        if self.state == State.Candidate:
            self.state = State.Follower
        print('recived heartbeat')
        response = {
            'term': self.term,
            'success': success
        }
        return raft.AppendEntriesResponse(**response)

    
    def GetLeader(self, request, context):
        if self.leader:
            leaderId = self.leader[0]
            address = self.leader[1]
        response = {
            'leaderId': leaderId,
            'address': address
        }
        return raft.GetLeaderResponse(**response)

    def Suspend(self, request, context):
        self.status = Status.Suspended
        print(f'Sleeping for {request.period} seconds.')
        time.sleep(request.period)
        return raft.SuspendResponse()
    
    def __send_heartbeat(self, addr):
        channel = grpc.insecure_channel(addr)
        stub = raft_grpc.RaftServiceStub(channel)
        request = {
            'leaderTerm': self.term,
            'leaderId': self.id
        }
        try:
            response = stub.AppendEntries(
                raft.AppendEntriesRequest(**request)
            )
            if response.term > self.term:
                self.term = response.term
                self.state = State.Follower
                self.counter = 0
            print('sent heartbeat')
        except:
            pass

    def __heartbeat_manager(self):
        print(f'I will send heartbeats. counter = {self.counter}')
        pool = [threading.Thread(target=self.__send_heartbeat, args=(_[1],))
            for _ in self.neighbours]
        for t in pool:
            t.start()
        for t in pool:
            t.join()

    def __start_timer(self):
        thread = threading.Thread(target=self.__timer)
        return thread

    def __timer(self):
        start_time = time.time()
        # while self.timer.is_alive:
        while True:
            if self.status == Status.Suspended:
                continue
            if self.counter % 50 == 0 and self.state == State.Leader:
                self.__update_on_time_limit()
                continue
            if self.counter > self.reset_time and self.state != State.Leader:
                self.__update_on_time_limit()
            self.__increase_counter()
            time.sleep(INTERVAL - ((time.time() - start_time) % INTERVAL))

    def __increase_counter(self):
        self.counter += 1

    def __update_on_time_limit(self):
        if self.state == State.Follower:
            # the follower will become a candidate 
            self.term += 1
            self.counter = 0
            self.state = State.Candidate
            print(f'I am a {self.state}. Term: {self.term}')
            # request votes from all other candidates
            self.__votes_collecting()
            return
        if self.state == State.Candidate:
            # the candidate will become a follower since the time is up
            self.reset_time = rnd.randint(150, 300) # ms
            self.counter = 0
            self.term += 1
            self.state = State.Follower
            print(f'I am a {self.state}. Term: {self.term}')
            return
        if self.state == State.Leader:
            self.counter = 0
            self.__heartbeat_manager()
        return
        # if the state was leader and a timeout happend, then it will skip it
    
    def __update_to_leader(self):
        self.state = State.Leader
        self.term += 1
        self.counter = 0
        self.leader = (self.id, self.address)
        print(f'I am a {self.state}. Term: {self.term}')

    def __votes_collecting(self):
        votes_count = 1
        start_time = time.time()
        for node in self.neighbours:
            channel = grpc.insecure_channel(node[1])
            stub = raft_grpc.RaftServiceStub(channel)
            request = {
                'candidateTerm': self.term,
                'candidateId': self.id,
            }
            try:
                response = stub.RequestVote(
                    raft.RequestVoteRequest(**request)
                )
                if response and response.result:
                    votes_count += 1
                if votes_count > len(self.neighbours) // 2:
                    self.__update_to_leader()
                    break
            except:
                pass
                # print('Couldn\'t connect to node...')
        
        print(f'time taken = {time.time() - start_time}, time = {time.time()}, start time = {start_time}')
        


def run(handler: Server):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_grpc.add_RaftServiceServicer_to_server(
        handler, server
    )
    server.add_insecure_port(f'[::]:{handler.address.split(":")[1]}')
    try:
        print(f"Server has been started with address {handler.address}")
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    
    neighbours = []
    id = int(sys.argv[1])
    address = None
    with open('config.conf') as conf:
        while s := conf.readline():
            n_ip, *n_address = s.split()
            if int(n_ip) == id:
                address = ':'.join(n_address)
            else:
                neighbours.append((int(n_ip), ':'.join(n_address)))
    try:
        run(Server(id, address, neighbours))
    except Exception as e:
        print(e)