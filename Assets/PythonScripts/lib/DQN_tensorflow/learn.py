import traceback
import tensorflow as tf

tf.keras.backend.set_floatx('float32')

# hyper parameters
GAMMA = 0.99
MIN_BUFFER_SIZE = 128
BATCH_SIZE = 32


def learn(model, target_model, replay_buffer, shared_vars):
    try:
        while shared_vars.running_sub_thread:
            if replay_buffer.size() < MIN_BUFFER_SIZE:
                continue
            for _ in range(BATCH_SIZE):
                states, actions, rewards, next_states, done = replay_buffer.sample()
                targets = target_model.predict(states)
                next_q_values = target_model.predict(next_states).max(axis=1)
                targets[range(BATCH_SIZE), actions] = rewards + \
                    (1 - done) * next_q_values * GAMMA
                model.train(states, targets)

            weights = model.model.get_weights()
            target_model.model.set_weights(weights)
            shared_vars.model_already_updated = True

    except Exception:
        print(traceback.format_exc())
        shared_vars.error_in_subthread = True
