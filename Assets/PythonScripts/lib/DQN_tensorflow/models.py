import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam
from collections import deque
import random


class SimpleDQN:
    def __init__(self, state_dim, action_dim, lr):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr

        self.model = self.create_model()

    def create_model(self):
        model = Sequential([
            Input((self.state_dim,)),
            Dense(64, activation='relu'),
            Dense(32, activation='relu'),
            Dense(self.action_dim)
        ])
        model.compile(loss='mse', optimizer=Adam(self.lr))
        return model

    def predict(self, state):
        return self.model.predict(state)

    def get_action(self, state, epsilon):
        state = np.reshape(state, [1, self.state_dim])
        q_value = self.predict(state)[0]
        if np.random.random() < epsilon:
            return random.randint(0, self.action_dim - 1)
        return np.argmax(q_value)

    def train(self, states, targets):
        self.model.fit(states, targets, epochs=1, verbose=0)


class ReplayBuffer:
    def __init__(self, batch_size=32, capacity=10000):
        self.buffer = deque(maxlen=capacity)
        self.batch_size = batch_size

    def put(self, state, action, reward, next_state, done):
        self.buffer.append([state, action, reward, next_state, done])

    def sample(self):
        sample = random.sample(self.buffer, self.batch_size)
        states, actions, rewards, next_states, done = map(
            np.asarray, zip(*sample))
        states = np.array(states).reshape(self.batch_size, -1)
        next_states = np.array(next_states).reshape(self.batch_size, -1)
        return states, actions, rewards, next_states, done

    def size(self):
        return len(self.buffer)
