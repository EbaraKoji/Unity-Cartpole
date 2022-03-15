import torch
import torch.nn as nn
import torch.optim as optim

import numpy as np
from collections import deque
import random


class SimpleDQN(nn.Module):
    def __init__(self, state_dim, action_dim, lr):
        super(SimpleDQN, self).__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, action_dim),
        )
        self.optimizer = optim.Adam(self.parameters(), lr=lr)

    def forward(self, x):
        return self.net(x.float())

    def get_action(self, state, epsilon, device='cpu'):
        if np.random.random() < epsilon:
            return random.randint(0, self.action_dim - 1)
        else:
            state_a = np.array([state], copy=False)
            state_v = torch.tensor(state_a).to(device)
            q_vals_v = self(state_v)
            _, act_v = torch.max(q_vals_v, dim=1)
            return int(act_v.item())


class ReplayBuffer:
    def __init__(self, batch_size=32, capacity=10000):
        self.buffer = deque(maxlen=capacity)
        self.batch_size = batch_size

    def put(self, state, action, reward, next_state, done):
        self.buffer.append([state, action, reward, next_state, done])

    def sample(self):
        indices = np.random.choice(
            len(self.buffer), self.batch_size, replace=False)
        states, actions, rewards, next_states, dones = zip(
            *[self.buffer[idx] for idx in indices])
        return np.array(states), np.array(actions), np.array(
            rewards, dtype=np.float32), np.array(next_states), np.array(
            dones, dtype=np.uint8)

    def size(self):
        return len(self.buffer)
