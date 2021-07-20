from typing import Any
from abc import ABC, abstractmethod

import numpy as np


class Augmenter(ABC):
    """ABC is the abstract base class for augmenter.
    """

    # custom augmenter
    _augmenter: Any

    def __init__(self):
        pass

    @abstractmethod
    def augment(self, audio: np.ndarray) -> np.ndarray:
        """ abstract method to augment signal."""
