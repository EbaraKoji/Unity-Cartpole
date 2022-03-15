import json
import socket
import time
import traceback
import typing  # noqa: F401
from threading import Thread, Event
import argparse
from importlib import import_module
import os

import numpy as np
import torch
# import torch.optim as optim

from lib.DQN_pytorch.learn import learn
from lib.DQN_pytorch.models import SimpleDQN, ReplayBuffer
from lib.data_types import ReqType, Request

# play_modeを設定したせいで全体的に条件分岐の見通しが悪い、要リファクタリング

parser = argparse.ArgumentParser()

parser.add_argument(
    '-mode',
    '--play_mode',
    default=0,  # 誤ってモデルを新規学習で更新してしまわないよう、defualtはplayに設定
    required=False,
    type=int,
    help='0: play on loaded model, \
            1: learn from loaded model and save, \
            2: new learn and save, \
            3: new learn and NOT save')

parser.add_argument(
    "--cuda",
    default=False,
    action="store_true",
    help="Enable cuda")

args = parser.parse_args()
device = torch.device("cuda" if args.cuda else "cpu")


HOST = '127.0.0.1'
PORT = 80
CONNECT_INTERVAL = 0.001

STATE_DIM = 4
ACTION_DIM = 2
LEARNING_RATE = 0.01

EPS_START = 1.0
EPS_DECAY = 0.9995
EPS_MIN = 0.01

MAX_EPISODE_REWARD = 500
AVERAGE_REWARD_COUNT = 10

LEARN_LOGIC = 'DQN_pytorch'
SAVE_DIR = f'lib/{LEARN_LOGIC}/saved'
MODEL_NAME = 'best_model'
BEST_MODEL_PATH = f'{SAVE_DIR}/{MODEL_NAME}.dat'
TMP_VAR_NAME = 'tmp_var'
TMP_VAR_PATH = f'{SAVE_DIR}/{TMP_VAR_NAME}.py'
# import_module用のpath
TMP_VAR_IMPORT_PATH = f'{SAVE_DIR.replace("/", ".")}.{TMP_VAR_NAME}'


# ToDo: A2Cなど他のロジックでも使えるよう拡張する
def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    epsilon = EPS_START
    episode_rewards = np.array([])
    episode_reward = 0
    best_average_reward = 0
    last_average_reward = None

    # load or create model, and load_tmps(if mode is 1)
    model = SimpleDQN(STATE_DIM, ACTION_DIM, LEARNING_RATE)
    target_model = SimpleDQN(STATE_DIM, ACTION_DIM, LEARNING_RATE)
    # optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    if args.play_mode == 0:
        model.load_state_dict(
            torch.load(
                BEST_MODEL_PATH,
                map_location=lambda storage,
                loc: storage))
    elif args.play_mode == 1:
        model.load_state_dict(
            torch.load(
                BEST_MODEL_PATH,
                map_location=lambda storage,
                loc: storage))
        target_model.load_state_dict(model.state_dict())
        best_average_reward, epsilon = load_tmps()

    if args.play_mode != 0:
        shared_vars = ShareVarsBetweenThreads(model)
        event = Event()
        replay_buffer = ReplayBuffer()
        t = Thread(
            target=learn,
            args=(
                shared_vars,
                target_model,
                replay_buffer,
                device))
        t.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    try:
        # 初期化処理
        make_reset_request(sock)
        res = recv_data(sock)
        deal_with_error(res)

        obs = dict_to_nparray(res['data'])
        done = False

        while True:
            if done:
                make_reset_request(sock)
                res = recv_data(sock)
                deal_with_error(res)

                episode_rewards = np.append(episode_rewards, episode_reward)
                episode_reward = 0

                # サンプル数が少ない学習初期はaverage_rewardを計算しない
                if args.play_mode != 0 and len(
                        episode_rewards) > AVERAGE_REWARD_COUNT:
                    # 直近Nエピソードの平均得点を計算してbestを更新したらモデルを保存
                    last_average_reward = episode_rewards[-AVERAGE_REWARD_COUNT:].mean(
                    )
                    if last_average_reward > best_average_reward:
                        print('best_average_rewards updated!')
                        print(
                            f'best_average_reward: {best_average_reward} -> {last_average_reward}')
                        best_average_reward = last_average_reward

                        if args.play_mode != 3 and shared_vars.model_already_updated:
                            torch.save(shared_vars.model.state_dict(), BEST_MODEL_PATH)

                obs = dict_to_nparray(res['data'])
                done = False
            else:
                action = shared_vars.model.get_action(obs, epsilon)
                if args.play_mode != 0:
                    epsilon = max(epsilon * EPS_DECAY, EPS_MIN)
                make_action_request(sock, int(action))
                res = recv_data(sock)
                deal_with_error(res)

                data = res['data']
                last_obs = obs
                obs = dict_to_nparray(data['obs'])
                reward = data['reward']
                done = data['done']

                episode_reward += reward

                if args.play_mode != 0:
                    replay_buffer.put(last_obs, action, reward, obs, done)

                if episode_reward >= MAX_EPISODE_REWARD:
                    done = True

            if args.play_mode != 0 and shared_vars.error_in_subthread:
                raise Exception

            # CONNECT_INTERVALが0だとUnityのUpdateのフレーム更新前に次のrequestが送られてしまうことがある
            time.sleep(CONNECT_INTERVAL)

    # ToDo: 通信エラー処理を書く

    except KeyboardInterrupt:
        print(traceback.format_exc())
        if args.play_mode != 0:
            shared_vars.running_sub_thread = False
    except Exception:
        print(traceback.format_exc())
        if args.play_mode != 0:
            shared_vars.running_sub_thread = False
    finally:
        # 通信停止などの処理でエラーが出る可能性もあるため、最初に各データを保存
        if args.play_mode == 1 or args.play_mode == 2:
            # 保存すべきデータがない時は更新しない
            if last_average_reward is not None:
                # ToDo: also save total steps
                f = open(TMP_VAR_PATH, 'w+')
                s = f'BEST_REWARD = {best_average_reward}\nEPSILON = {epsilon}\n'
                f.write(s)
                f.close()
                print('saved tmps.')

        print('closing connection...')
        sock.close()

        if args.play_mode != 0:
            event.set()
            shared_vars.running_sub_thread = False  # noqa F841
            t.join()


def recv_data(s: socket):
    res = s.recv(1024).decode('UTF-8')
    if len(res) == 0:
        return
    return json.loads(res)


def make_reset_request(s: socket):
    request = Request(
        ReqType.Reset,
        time.time() * 1000,
        data={})
    s.sendall(request.to_json().encode('UTF-8'))


def make_action_request(s: socket, action: int):
    request = Request(
        ReqType.Action,
        time.time() * 1000,
        data=action)
    s.sendall(request.to_json().encode('UTF-8'))


def dict_to_nparray(dict):
    return np.array(list(dict.values()))


def deal_with_error(res):
    if res['statusCode'] != 200:
        # ToDo: csファイルの個別のエラーメッセージを書く
        # print(res['message'])
        print(res)
        raise Exception


def load_tmps():
    tmps = import_module(TMP_VAR_IMPORT_PATH)
    best_reward = tmps.BEST_REWARD
    epsilon = tmps.EPSILON
    return best_reward, epsilon


class ShareVarsBetweenThreads:
    def __init__(self, model):
        self.running_sub_thread = True
        self.model_already_updated = False
        self.error_in_subthread = False
        self.model = model


if __name__ == '__main__':
    main()
