import zmq
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('ports', help='tcp port of the server', type=int, nargs=2)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig()


def gcd(a: int, b: int) -> int:
    '''
    Return greatest common divider.
    '''

    assert a > 0 and b > 0

    a, b = sorted([a, b])
    while b > 0:
        if a > b:
            a = a - b
        else:
            b = b - a
    return a

def main():
    args = parser.parse_args()
    workers_in, workers_out = args.ports

    context = zmq.Context()

    logger.info(f'Starting the {__file__}...')

    sock_in = context.socket(zmq.SUB)
    sock_in.connect(f'tcp://127.0.0.1:{workers_in}')
    sock_in.setsockopt_string(zmq.SUBSCRIBE, 'gcd')
    sock_in.RCVTIMEO = 100

    sock_out = context.socket(zmq.PUB)
    sock_out.connect(f'tcp://127.0.0.1:{workers_out}')

    logger.info(f'Worker has been started!')

    while True:
        try:
            msg = sock_in.recv_string()
            a, b = map(int, msg.split()[1:])
            logger.info(f'Task has been obtained...{msg}')
            sock_out.send_string(f'GCD of {a} and {b} is {str(gcd(a, b))}')
            logger.info('Task is done!')
        except zmq.Again:
            pass


if __name__ == '__main__':
    main()