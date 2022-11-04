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
from threading import Timer, Event, Lock, Thread


timer_lock = Event()
term_lock = Lock()


class State(Enum):
    Follower = 1,
    Candidate = 2,
    Leader = 3


class Status(Enum):
    Suspended = 1,
    Running = 2


class Address:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port


class Server:
    def __init__(self, id: int, address: Address, neighbours: list[Address]):
        self.state = State.Follower # default state
        self.status = Status.Running # default status
        self.term = 0 # default term
        self.id = id
        self.address = address
        self.neighbours = neighbours
        self.last_vote_term = -1 # default vote
        self.start()
    
    def start(self):
        self.initialize_timer()
        self.timer.start()
    
    def initialize_timer(self):
        """Assign time interval for the timer. Initialize timer.
        """
        self.timer_interval = rnd.randint(150, 300) / 1000
        self.timer = Timer(self.timer_interval, self.follower_timer)

    def follower_timer(self):
        """Wait for to become a candidate. Reset if event is occured.
        """
        # TODO
        # while not timer_lock.is_set():
        if self.state == State.Follower:
            if self.timer.finished:
                print(f"Become a candidate, id #{self.id}")
                self.become_candidate()
                self.start_election()
            else:
                print(f"Call every {self.timer_interval} second, id #{self.id}")
                self.timer = Timer(self.timer_interval, self.follower_timer)
                self.timer.start()

    def reinitialize_timer(self):
        """Assign new time interval.
        """
        self.timer_interval = rnd.randint(150, 300) / 100

    def reset_timer(self):
        """Cancel current runnig timer and start it again.
        """
        if self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(self.timer_interval, self.follower_timer)
        self.timer.start()

    def update_term(self):
        with term_lock:
            self.term += 1

    def update_state(self, state: State):
        """Take a new state due to some events.
        """
        self.state = state

    def update_vote(self, term):
        """Vote for someone on this term.
        """
        if self.last_vote_term < term:
            self.last_vote_term = term

    def become_candidate(self):
        self.update_state(State.Candidate)
        self.update_term()

    def start_election(self):
        """Collect votes from neighbours and itself.
        Becomes Leader if possible.
        """
        if self.state != State.Candidate:
            return

        requests = []
        votes = [0 for _ in range(len(self.neighbours))]
        for n in self.neighbours:
            thread = Thread(target=self.request_vote, args=(n, votes))
            requests.append(thread)
            thread.start()
        
        for thread in requests:
            thread.join()
        
        if self.state != State.Candidate:
            return
        
        print(votes)
        if sum(votes) >= len(votes) // 2 + 1:
            self.become_leader()
        else:
            self.update_state(State.Follower)
            self.reinitialize_timer()
            self.reset_timer()

    def become_leader(self):
        print(f"Become a leader, id #{self.id}")
        if self.state == State.Candidate:
            self.update_state(State.Leader)
            # TODO
        # become follower self.become_follower()


    def request_vote(self, n, votes):
        # stub from grpc
        # self.last_vote_term = 1 # TODO, mock
        # votes[rnd.randint(0, 2)] = 1
        # return 1
        pass

    # def is_running(func):
    #     def wrapper(self):
    #         func(self)
    # TODO decorator to check if server is suspended

server = Server(0, Address("127.0.0.1", 5000), [])
server_2 = Server(1, Address("127.0.0.1", 5002), [])
server_3 = Server(2, Address("127.0.0.1", 5003), [])
adrs = (server.address, server_2.address, server_3.address)
server.neighbours = server_2.neighbours = server_3.neighbours = adrs
server.start()
server_2.start()
server_3.start()


# # FIXME
# # PROBABLY INJECT THIS SERVICE INTO SERVER CLASS
# class RaftServiceHandler(raft_grpc.RaftServiceServicer):
#     def __init__(self, id: int, address: str, neighbours: list[tuple]):
#         """
#         Makes a Server instance.

#         :param id: id of the server
#         :param address: address in form of <ip:port>
#         :param neighbours: list of (id, address) tuples
#         """
#         super().__init__()
#         self.id = id
#         self.address = address
#         self.neighbours = neighbours
#         # self.queue = Queue(len(neighbours))
#         self.state = State.Follower
#         self.term = 0
#         self.reset_time = rnd.randint(150, 300) # ms
#         self.counter = 0 # timer counter
#         self.leader: Union[tuple, None] = None # (id, address) of leader
#         self.isVoted = False
#         self.status = Status.Running
#         # self.timer = self.__start_timer().start()
#         self.__start_timer().start()
    
#     def RequestVote(self, request, context):
#         candidate_term = request.candidateTerm
#         candidate_id = request.candidateId
#         result = False

#         if candidate_term == self.term and not self.isVoted:
#             self.isVoted = True
#             result = True
#         if candidate_term > self.term:
#             self.term = candidate_term
#             self.isVoted = True
#             result = True
        
#         self.counter = 0 # you will always reset the timer
#         if self.state == State.Candidate or self.state == State.Leader and result:
#             self.term += 1
#             self.isVoted = False
#             self.state = State.Follower

#         response = {
#             'term': self.term,
#             'result': result
#         }
#         return raft.RequestVoteResponse(**response)

#     def AppendEntries(self, request, context):
#         term = request.term
#         leader_id = request.leaderId
#         success = True if term >= self.term else False
#         self.counter = 0
#         if self.state == State.Candidate:
#             self.state = State.Follower

#         response = {
#             'term': self.term,
#             'success': success
#         }
#         return raft.AppendEntriesResponse(**response)

    
#     def GetLeader(self, request, context):
#         if self.leader:
#             leaderId = self.leader[0]
#             address = self.leader[1]
#         response = {
#             'leaderId': leaderId,
#             'address': address
#         }
#         return raft.GetLeaderResponse(**response)

#     def Suspend(self, request, context):
#         self.status = Status.Suspended
#         print(f'Sleeping for {request.period} seconds.')
#         time.sleep(request.period)
#         return raft.SuspendResponse()
    
#     def __send_heartbeat(self, addr):
#         channel = grpc.insecure_channel(addr)
#         stub = raft_grpc.RaftServiceStub(channel)
#         request = {
#             'leaderTerm': self.term,
#             'leaderId': self.id
#         }
#         try:
#             response = stub.AppendEntries(
#                 raft.AppendEntriesRequest(**request)
#             )
#             if response.term > self.term:
#                 self.term = response.term
#                 self.state = State.Follower
#                 self.counter = 0
#         except:
#             pass
#             # print('Couldn\'t connect to node...')

#     def __heartbeat_manager(self):
#         pool = [threading.Thread(target=self.__send_heartbeat, args=(_[1],))
#             for _ in self.neighbours]
#         for t in pool:
#             t.start()
#         for t in pool:
#             t.join()

#     def __start_timer(self):
#         thread = threading.Thread(target=self.__timer)
#         return thread

#     def __timer(self):
#         start_time = time.time()
#         # while self.timer.is_alive:
#         while True:
#             if self.status == Status.Suspended:
#                 continue
#             if self.counter > 50 and self.state == State.Leader:
#                 self.__update_on_time_limit()
#                 continue
#             if self.counter > self.reset_time:
#                 self.__update_on_time_limit()
#             self.__increase_counter()
#             time.sleep(INTERVAL - ((time.time() - start_time) % INTERVAL))

#     def __increase_counter(self):
#         self.counter += 1

#     def __update_on_time_limit(self):
#         print(self.state)
#         if self.state == State.Follower:
#             # the follower will become a candidate 
#             self.term += 1
#             self.counter = 0
#             self.state = State.Candidate
#             # request votes from all other candidates
#             self.__votes_collecting()
#             return
#         if self.state == State.Candidate:
#             # the candidate will become a follower since the time is up
#             self.reset_time = rnd.randint(150, 300) # ms
#             self.counter = 0
#             self.term += 1
#             self.state = State.Follower
#             return
#         if self.state == State.Leader:
#             self.__heartbeat_manager()
#         return
#         # if the state was leader and a timeout happend, then it will skip it
    
#     def __update_to_leader(self):
#         print(self.state)
#         self.state = State.Leader
#         self.term += 1
#         self.counter = 0
#         self.leader = (self.id, self.address)

#     def __votes_collecting(self):
#         votes_count = 1
#         for node in self.neighbours:
#             channel = grpc.insecure_channel(node[1])
#             stub = raft_grpc.RaftServiceStub(channel)
#             request = {
#                 'candidateTerm': self.term,
#                 'candidateId': self.id,
#             }
#             try:
#                 response = stub.RequestVote(
#                     raft.RequestVoteRequest(**request)
#                 )
#                 if response and response.result:
#                     votes_count += 1
#                 if votes_count > len(self.neighbours) // 2:
#                     self.__update_to_leader()
#             except:
#                 pass
#                 # print('Couldn\'t connect to node...')


# def run(handler: RaftServiceHandler):
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#     raft_grpc.add_RaftServiceServicer_to_server(
#         handler, server
#     )
#     server.add_insecure_port(f'[::]:{handler.address.split(":")[1]}')
#     try:
#         print(f"Server has been started with address {handler.address}")
#         server.start()
#         server.wait_for_termination()
#     except KeyboardInterrupt:
#         exit()


# if __name__ == "__main__":
    
#     neighbours = []
#     id = int(sys.argv[1])
#     address = None
#     with open('config.conf') as conf:
#         while s := conf.readline():
#             n_ip, *n_address = s.split()
#             if int(n_ip) == id:
#                 address = ':'.join(n_address)
#             else:
#                 neighbours.append((int(n_ip), ':'.join(n_address)))
#     try:
#         run(RaftServiceHandler(id, address, neighbours))
#     except Exception as e:
#         print(e)