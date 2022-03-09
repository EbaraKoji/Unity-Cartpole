import numpy as np
from collections import deque

# ToDo: 計算速度を考慮してfloat32をfloat16に変換する。parameterの更新(model.train)直前で行う

# hyper parameters
GAMMA = 0.99
BATCH_SIZE = 32


class ReplayBuffer:
    def __init__(self, capacity=10000, batch_size=BATCH_SIZE):
        self.buffer = deque(maxlen=capacity)
        self.batch_size = batch_size

    def put(self, state, action, reward, next_state, done):
        self.buffer.append([state, action, reward, next_state, done])

    def sample(self):
        sample = np.random.sample(self.buffer, self.batch_size)
        states, actions, rewards, next_states, done = map(
            np.asarray, zip(*sample))
        states = np.array(states).reshape(self.batch_size, -1)
        next_states = np.array(next_states).reshape(self.batch_size, -1)
        return states, actions, rewards, next_states, done

    def size(self):
        return len(self.buffer)


def learn(model, target_model, replay_buffer, running):
    while running:
        if replay_buffer.size() >= BATCH_SIZE:
            for _ in range(10):
                states, actions, rewards, next_states, done = replay_buffer.sample()
                targets = target_model.predict(states)
                next_q_values = target_model.predict(next_states).max(axis=1)
                targets[range(BATCH_SIZE), actions] = rewards + (1 - done) * next_q_values * GAMMA
                model.train(states, targets)

        weights = model.model.get_weights()
        target_model.model.set_weights(weights)

    
