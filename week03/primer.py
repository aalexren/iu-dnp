import zmq
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('ports', help='tcp port of the server', type=int, nargs=2)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig()


def isprime(a: int) -> bool:
    '''
    Return if number is a prime number.
    Eratosphen's sieve algorithm.
    '''

    assert a >= 0

    if a in [0, 1]:
        return False

    primes = [bool(_ % 2) for _ in range(a + 1)]
    primes[:3] = [False, False, True]

    # iterate over the odd number only
    for i in [i for i in range(3, a + 1) if i * i <= a and i % 2]:
        # start from the i^2 and check every next +i number
        for j in [j for j in range(i * i, a + 1, i)]:
            primes[j] = False
    
    return primes[a]

    

def main():
    args = parser.parse_args()
    workers_in, workers_out = args.ports

    context = zmq.Context()

    logger.info(f'Starting the {__file__}...')

    sock_in = context.socket(zmq.SUB)
    sock_in.connect(f'tcp://127.0.0.1:{workers_in}')
    sock_in.setsockopt_string(zmq.SUBSCRIBE, 'isprime')
    sock_in.RCVTIMEO = 100

    sock_out = context.socket(zmq.PUB)
    sock_out.connect(f'tcp://127.0.0.1:{workers_out}')

    logger.info(f'Worker has been started!')

    while True:
        try:
            msg = sock_in.recv_string()
            logger.info(f'Task has been obtained...{msg}')
            a = int(msg.split()[1])
            sock_out.send_string(f'{a} is{(not isprime(a)) * " not"} prime number')
            logger.info('Task is done!')
        except zmq.Again:
            pass


if __name__ == '__main__':
    main()