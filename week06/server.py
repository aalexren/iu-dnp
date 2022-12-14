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
state_lock = Lock()


class State(Enum):
    Follower = 1,
    Candidate = 2,
    Leader = 3


class Status(Enum):
    Suspended = 1,
    Running = 2


class Address:
    def __init__(self, id: int, ip: str, port: int):
        self.id = id
        self.ip = ip
        self.port = port

    def __repr__(self):
        return f"<{self.id} => {self.ip}:{self.port}>"


class Server:
    def __init__(self, id: int, address: Address, neighbours):
        self.state = State.Follower  # default state
        self.status = Status.Running  # default status
        self.term = 0  # default term
        self.id = id
        self.address = address
        self.neighbours = neighbours
        self.last_vote_term = -1  # default vote
        self.leader_id = self.id  # default
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
        if self.state == State.Follower and self.status == Status.Running:
            if self.timer.finished:
                print("The leader is dead")
                self.become_candidate()
                self.start_election()

    def reinitialize_timer(self):
        """Assign new time interval.
        """
        self.timer_interval = rnd.randint(150, 300) / 1000

    def reset_timer(self):
        """Cancel current runnig timer and start it again.
        """
        self.timer.cancel()
        self.timer = Timer(self.timer_interval, self.follower_timer)
        self.timer.start()

    def update_term(self):
        with term_lock:
            self.term += 1

    def update_term_t(self, t):
        with term_lock:
            self.term = t

    def update_state(self, state: State):
        """Take a new state due to some events.
        """
        with state_lock:
            self.state = state

    def update_vote(self, term):
        """Vote for someone on this term.
        """
        if self.last_vote_term < term:
            self.last_vote_term = term

    def become_candidate(self):
        self.update_state(State.Candidate)
        self.update_term()
        print(f"I am a candidate. Term: {self.term}")

    def start_election(self):
        """Collect votes from neighbours and itself.
        Becomes Leader if possible.
        """
        if self.status == Status.Suspended:
            return

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
        print("Votes received")

        if sum(votes) > len(votes) // 2:
            self.become_leader()
        else:
            print(f"I am a follower. Term: {self.term}")
            self.update_state(State.Follower)
            self.reinitialize_timer()
            self.reset_timer()

    def request_vote(self, addr: Address, votes):
        if self.status == Status.Suspended:
            return

        channel = grpc.insecure_channel(f"{addr.ip}:{addr.port}")
        stub = raft_grpc.RaftServiceStub(channel)
        if self.state != State.Candidate:
            return
        request = {
            'candidateTerm': self.term,
            'candidateId': self.id,
        }
        try:
            response = stub.RequestVote(
                raft.RequestVoteRequest(**request)
            )
            if response.term > self.term:
                self.term = response.term
                self.become_follower()
            elif response.result and response.term <= self.term:
                votes[addr.id] = 1
        except:
            pass

    def become_follower(self):
        print(f"I am a follower. Term: {self.term}")
        self.update_state(State.Follower)
        self.reset_timer()

    def become_leader(self):
        if self.status == Status.Suspended:
            return

        if self.state == State.Candidate:
            self.update_state(State.Leader)
            self.heartbeat_timer()
            self.leader_id = self.id
            print(f"I am a leader. Term: {self.term}")

    def send_heartbeat(self, addr):
        if self.status == Status.Suspended:
            return

        channel = grpc.insecure_channel(f"{addr.ip}:{addr.port}")
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
                print(f"I am a follower. Term: {self.term}")
                self.update_state(State.Follower)
        except:
            pass

    def heartbeat_timer(self):
        if self.status == Status.Suspended:
            return

        if self.state != State.Leader:
            return
        pool = []
        for n in self.neighbours:
            if n.id != MY_ADDR.id:
                thread = Thread(target=self.send_heartbeat, args=(n,))
                thread.start()
                pool.append(thread)

        for t in pool:
            t.join()

        self.leader_timer = Timer(50 / 1000, self.heartbeat_timer)
        self.leader_timer.start()

    def suspend_loop(self, period):
        self.status = Status.Suspended
        self.timer.cancel()
        self.timer = Timer(period, self.sleep)
        self.timer.start()

    def sleep(self):
        self.status = Status.Running
        if self.state == State.Leader:
            self.heartbeat_timer()
        elif self.state == State.Candidate:
            self.start_election()
        else:
            self.reset_timer()


class RaftServiceHandler(raft_grpc.RaftServiceServicer, Server):
    def __init__(self, id: int, address: Address, neighbours):
        super().__init__(id, address, neighbours)
        print(f"The server starts at {address.ip}:{address.port}")
        print(f"I am a follower. Term: {self.term}")

    def RequestVote(self, request, context):
        if self.status == Status.Suspended:
            msg = 'The server is currently suspended. Try again later.'
            context.set_details(msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return raft.RequestVoteResponse()

        candidate_term = request.candidateTerm
        candidate_id = request.candidateId
        result = False

        if candidate_term == self.term and self.last_vote_term < candidate_term:
            self.last_vote_term = candidate_term
            result = True
        if candidate_term > self.term:
            self.term = candidate_term
            self.last_vote_term = candidate_term
            result = True

        if result and candidate_id != MY_ADDR.id:
            self.become_follower()
            self.reset_timer()
            self.leader_id = candidate_id

        if result:
            print(f"Voted for node {candidate_id}")

        response = {
            'term': self.term,
            'result': result
        }
        return raft.RequestVoteResponse(**response)

    def AppendEntries(self, request, context):
        if self.status == Status.Suspended:
            msg = 'The server is currently suspended. Try again later.'
            context.set_details(msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return raft.AppendEntriesResponse()

        term = request.leaderTerm
        leader_id = request.leaderId
        success = True if term >= self.term else False

        if success and self.id != leader_id:
            self.reset_timer()
            if self.state != State.Follower:
                self.become_follower()
            self.leader_id = leader_id

        response = {
            'term': self.term,
            'success': success
        }
        return raft.AppendEntriesResponse(**response)

    def GetLeader(self, request, context):
        if self.status == Status.Suspended:
            msg = 'The server is currently suspended. Try again later.'
            context.set_details(msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return raft.GetLeaderResponse()

        print('Command from client: getleader')
        print(f'{self.leader_id} {self.neighbours[self.leader_id].ip}:{self.neighbours[self.leader_id].port}')
        response = {
            'leaderId': self.leader_id,
            'address': f'{self.neighbours[self.leader_id].ip}:{self.neighbours[self.leader_id].port}'
        }
        return raft.GetLeaderResponse(
            **response
        )

    def Suspend(self, request, context):
        if self.status == Status.Suspended:
            msg = 'The server is currently suspended. Try again later.'
            context.set_details(msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return raft.SuspendResponse()

        print(f'Command from client: suspend {request.period}')
        self.suspend_loop(request.period)
        print(f'Sleeping for {request.period} seconds.')

        return raft.SuspendResponse(**{})


def run(handler: RaftServiceHandler):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_grpc.add_RaftServiceServicer_to_server(
        handler, server
    )
    server.add_insecure_port(f'[::]:{handler.address.port}')
    try:
        # print(f"Server has been started with address {handler.address}")
        server.start()
        server.wait_for_termination()
    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    global MY_ADDR
    neighbours = []
    id = int(sys.argv[1])
    address = None
    with open('config.conf') as conf:
        while s := conf.readline():
            n_id, *n_address = s.split()
            if int(n_id) == id:
                address = Address(int(n_id), n_address[0], int(n_address[1]))
                MY_ADDR = address

            n_ip = n_address[0]
            n_port = int(n_address[1])
            neighbours.append(Address(int(n_id), n_ip, n_port))
    try:
        pass
        run(RaftServiceHandler(id, address, neighbours))
    except Exception as e:
        print(e)

MY_ADDR = None
