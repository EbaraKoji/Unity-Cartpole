import json
import socket
import time
import traceback
import typing  # noqa: F401
from threading import Thread, Event

import numpy as np

from lib.DQN.learn import learn
from lib.DQN.models import SimpleDQN, ReplayBuffer
from data_types import ReqType, Request

HOST = '127.0.0.1'
PORT = 80
CONNECT_INTERVAL = 0.001
REALTIME_LEARN = True

STATE_DIM = 4
ACTION_DIM = 2
LERNING_RATE = 0.01

EPS_START = 1.0
EPS_DECAY = 0.995
EPS_MIN = 0.02


def recv_data(s: socket):
    res = s.recv(1024).decode('UTF-8')
    if len(res) == 0:
        return
    return json.loads(res)


def main():
    # リアルタイム学習を行う場合は、別スレッドで学習処理ファイルを実行
    epsilon = EPS_START
    model = SimpleDQN(STATE_DIM, ACTION_DIM, LERNING_RATE)
    target_model = SimpleDQN(STATE_DIM, ACTION_DIM, LERNING_RATE)
    # model.load_weights(LOAD_FILE)

    if REALTIME_LEARN:
        event = Event()
        replay_buffer = ReplayBuffer()
        running = True
        t = Thread(target=learn, args=(model, target_model, replay_buffer, running))
        t.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    try:
        # 初期化処理
        make_reset_request(sock)
        res = recv_data(sock)
        if res["statusCode"] != 200:
            print(res)
            raise Exception

        obs = dict_to_nparray(res["data"])
        done = False

        while True:
            if done:
                make_reset_request(sock)
                res = recv_data(sock)
                if res["statusCode"] != 200:
                    print(res)
                    raise Exception

                obs = dict_to_nparray(res["data"])
                done = False
            else:
                action = model.get_action(obs, epsilon)
                if REALTIME_LEARN:
                    epsilon = max(epsilon * EPS_DECAY, EPS_MIN)
                make_action_request(sock, int(action))
                res = recv_data(sock)
                if res["statusCode"] != 200:
                    print(res)
                    raise Exception

                data = res["data"]
                last_obs = obs
                obs = dict_to_nparray(data["obs"])
                reward = data["reward"]
                done = data["done"]

                if REALTIME_LEARN:
                    replay_buffer.put(last_obs, action, reward, obs, done)

            time.sleep(CONNECT_INTERVAL)

    # ToDo: 通信エラー処理を書く

    except KeyboardInterrupt:
        print(traceback.format_exc())
        running = False

    finally:
        print('closing connection...')
        sock.close()
        # リアルタイム学習を行う場合は、スレッドを停止
        if REALTIME_LEARN:
            event.set()
            running = False
            t.join()


def make_reset_request(s: socket):
    request = Request(
        ReqType.Reset,
        time.time() * 1000,
        status_code=200,
        data={})
    s.sendall(request.to_json().encode('UTF-8'))


def make_action_request(s: socket, action: int):
    request = Request(
        ReqType.Action,
        time.time() * 1000,
        status_code=200,
        data=action)
    s.sendall(request.to_json().encode('UTF-8'))


def dict_to_nparray(dict):
    return np.array(list(dict.values()))


if __name__ == "__main__":
    main()
