from typing import Any, Dict
from abc import ABC, abstractmethod

import numpy as np


class Separator(ABC):
    """ABC is the abstract base class for music
    separation.
    """

    # custom separator
    _separator: Any

    def __init__(self):
        pass

    @abstractmethod
    def separate(self, audio_file: np.ndarray) -> Dict[str, np.ndarray]:
        """ abstract method to separate signal."""
