import zmq
import argparse
import logging
import re

parser = argparse.ArgumentParser()
parser.add_argument('ports', help='tcp port of the server', type=int, nargs=4)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig()

def main():
    args = parser.parse_args()
    clients_in, clients_out, workers_in, workers_out = args.ports

    context = zmq.Context()

    logger.info('Starting the server...')

    sock_cl_in = context.socket(zmq.REP)
    sock_cl_in.bind(f'tcp://127.0.0.1:{clients_in}')

    sock_cl_out = context.socket(zmq.PUB)
    sock_cl_out.bind(f'tcp://127.0.0.1:{clients_out}')

    sock_wk_in = context.socket(zmq.PUB)
    sock_wk_in.bind(f'tcp://127.0.0.1:{workers_in}')

    sock_wk_out = context.socket(zmq.SUB)
    sock_wk_out.bind(f'tcp://127.0.0.1:{workers_out}')
    sock_wk_out.setsockopt_string(zmq.SUBSCRIBE, '')
    sock_wk_out.RCVTIMEO = 100

    logger.info('Server works!')

    cmds = ['isprime', 'gcd']
    while True:
        try:
            # get new message
            # if it is a command pass it to worker
            msg = sock_cl_in.recv().decode('utf-8')
            logger.info(f'"{msg}" was received')
            sock_cl_in.send_string('') # must send back to enable next state
            
            if any([re.match(r'^isprime \d+$', msg) or re.match(r'^gcd \d+ \d+$', msg)]):
                # get result from worker and send it back to clients
                logger.info(f'Send task {msg} to worker...')
                sock_wk_in.send_string(msg)
                work_res = sock_wk_out.recv_string()
                sock_cl_out.send_string(work_res)
                logger.info(f'Getting result from worker = {work_res}')
            else:
                sock_cl_out.send_string(msg)
        except zmq.Again:
            pass


if __name__ == '__main__':
    main()