import traceback
import torch
import torch.nn as nn

GAMMA = 0.99
TARGET_SYNC_COUNT = 10
BATCH_SIZE = 32


def learn(shared_vars, target_model, replay_buffer, device):
    try:
        while shared_vars.running_sub_thread:
            for _ in range(TARGET_SYNC_COUNT):
                if replay_buffer.size() < BATCH_SIZE:
                    continue

                shared_vars.model.optimizer.zero_grad()
                batch = replay_buffer.sample()
                loss_t = calc_loss(batch, shared_vars.model, target_model, device=device)
                loss_t.backward()
                shared_vars.model.optimizer.step()

            target_model.load_state_dict(shared_vars.model.state_dict())
            shared_vars.model_already_updated = True

    except Exception:
        print(traceback.format_exc())
        shared_vars.error_in_subthread = True


def calc_loss(batch, model, tgt_model, device="cpu"):
    states, actions, rewards, next_states, dones = batch

    states_v = torch.tensor(states).to(device)
    next_states_v = torch.tensor(next_states).to(device)
    actions_v = torch.tensor(actions).to(device)
    rewards_v = torch.tensor(rewards).to(device)
    done_mask = torch.ByteTensor(dones).to(device)
    state_action_values = model(states_v).gather(
        1, actions_v.unsqueeze(-1)).squeeze(-1)
    next_state_values = tgt_model(next_states_v).max(1)[0]
    next_state_values[done_mask] = 0.0

    # detach: tgt_modelにはbackpropagationが及ばないようにする
    next_state_values = next_state_values.detach()

    expected_state_action_values = next_state_values * GAMMA + rewards_v
    loss = nn.MSELoss()(state_action_values, expected_state_action_values)
    return loss
