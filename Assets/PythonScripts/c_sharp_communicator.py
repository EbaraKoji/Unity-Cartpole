import json
import socket
import time
import typing  # noqa: F401

HOST = '127.0.0.1'
PORT = 80

CONNECT_INTERVAL = 0.5


def send_data(s: socket, data):
    s.sendall((json.dumps(data).encode('UTF-8')))


def recv_data(s: socket):
    res = s.recv(1024).decode('UTF-8')
    if len(res) == 0:
        return
    return json.loads(res)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    try:
        while True:
            data = {
                "type": "dict",
                "int": 1,
                "float": 0.5,
            }
            send_data(sock, data)
            res = recv_data(sock)
            print(res)
            time.sleep(CONNECT_INTERVAL)

    except KeyboardInterrupt:
        print('closing connection...')
        sock.close()


if __name__ == "__main__":
    main()
