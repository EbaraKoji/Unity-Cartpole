import json
import typing  # noqa: F401
import numpy as np
from enum import Enum


class Obs:
    def __init__(self, obs_array):
        assert isinstance(obs_array, np.ndarray)
        assert obs_array.shape == (4,)

        self.cartPositionX = obs_array[0]
        self.cartVelocityX = obs_array[1]
        self.poleAngle = obs_array[2]
        self.poleAngularVelocity = obs_array[3]


class Action(Enum):
    Right = 0
    Left = 1


class ReqType(Enum):

    GetObs = 0
    GetParams = 1
    SetParams = 2
    Reset = 3
    Action = 4
    Close = 5


class Request():
    def __init__(self,
                 req_type: ReqType,
                 timestamp: int,
                 data: dict):
        self.req_type = req_type.value
        self.timestamp = timestamp
        self.data = data

    def to_json(self):
        json_data = {
            "reqType": self.req_type,
            "timestamp": self.timestamp,
            "data": self.data
        }
        return json.dumps(json_data)
