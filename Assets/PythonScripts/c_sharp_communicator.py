import socket
import time
from enum import Enum
import typing  # noqa: F401

HOST = '127.0.0.1'
PORT = 80

CONNECT_INTERVAL = 0.5


class SendType(Enum):
    STRING = 0
    INT = 1
    FLOAT = 2


class ReceiveType(Enum):
    STRING = 0
    INT = 1
    FLOAT = 2
    INT_ARRAY = 3
    FLOAT_ARRAY = 4
    FLOAT_NDARRAY = 5


def send_data(s, send_type: SendType, data):
    if send_type == SendType.STRING:
        s.sendall((data.encode('UTF-8')))


def recv_data(s, receive_type: ReceiveType):
    if receive_type == ReceiveType.STRING:
        receive_data = s.recv(1024).decode('UTF-8')
        if len(receive_data) == 0:
            return
        print(receive_data)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    try:
        while True:
            send_message = str(time.time())
            send_data(sock, SendType.STRING, send_message)
            recv_data(sock, ReceiveType.STRING)
            time.sleep(CONNECT_INTERVAL)

    except KeyboardInterrupt:
        close_message = "stop connection"
        send_data(sock, SendType.STRING, close_message)
        print('closing connection...')
        sock.close()


if __name__ == "__main__":
    main()
