import zmq
import argparse
import logging


parser = argparse.ArgumentParser()
parser.add_argument('ports', help='tcp ports of the server [in, out]', type=int, nargs=2)
args = parser.parse_args()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig()

def main():
    clients_in, clients_out = args.ports

    context = zmq.Context()

    logger.info('Connecting to the server!')

    sock_in = context.socket(zmq.REQ)
    sock_in.connect(f'tcp://127.0.0.1:{clients_in}')

    sock_out = context.socket(zmq.SUB)
    sock_out.connect(f'tcp://127.0.0.1:{clients_out}')
    sock_out.setsockopt_string(zmq.SUBSCRIBE, '') # get all messages
    
    # Вообще говоря, это костыль, потому что если
    # зависит от времени ожидания, то такое 
    # приложение будет очень ненадёжным.
    # В лекции не сказано, как это исправить,
    # в лабе тоже. Придётся смотреть где-то ещё.
    sock_out.RCVTIMEO = 100 # time to wait for


    logger.info('Connection is established!')

    try:
        while True:
            msg = input('> ')
            if msg:
                sock_in.send_string(msg)
                sock_in.recv()
            try:
                res = sock_out.recv_string()
                logger.info(f'Result has been obtained: {res}')
            except zmq.Again:
                pass
    except KeyboardInterrupt:
        logger.exception('Terminate program...')
        exit(0)


if __name__ == '__main__':
    main()