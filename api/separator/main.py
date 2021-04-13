from enum import Enum
import numpy as np

from api.separator import SpleeterSeparator


class SignalType(str, Enum):
    Speech: str = "Speech"
    Music: str = "Music"


def separate(signal: np.ndarray, signal_type: SignalType, *args, **kwargs):
    if signal_type == SignalType.Speech:
        pass
    elif signal_type == SignalType.Music:
        separator = SpleeterSeparator(stems=2, *args, **kwargs)
        stems = separator.separate(signal)
    return stems
