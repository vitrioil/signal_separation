import torch
import torchaudio
import numpy as np

from typing import List, Any, Dict, Tuple, TypeVar
from dataclasses import dataclass

from api.schemas import Volume, Copy, BaseAugment, Augmentation


@dataclass
class AudioEffectParameters:
    effect_name: str
    duration: Tuple[float, float]
    effect_params: Dict[str, Any]


def to_tensor(audio: np.ndarray):
    return torch.from_numpy(audio)


T = TypeVar("T", bound="AudioEffectHelper")


class AudioEffectHelper:
    """Helper class for all torchaudio effects.

        Example use:
        >>>affect = AudioEffectHelper()
        >>>affect.vol('0.1', (0, 10)).vol('0.2', 30, 40)
        >>>effect = affect.apply(audio_tensor, sample_rate)
    """

    def __init__(self):
        self.effects = []

    def vol(self, gain: str, duration: Tuple[float, float] = None) -> T:
        """SoX: Apply an amplification or an attenuation to the audio signal.

            Args:
                gain (str): type of gain could be amplitude / power or dB.
                duration (tuple[float, float]): affected time interval.
                    Keep None to apply for entire signal
        """
        self.effects.append(
            AudioEffectParameters("vol", duration, {"gain": gain})
        )
        return self

    def _apply_interval(
        self,
        audio: torch.Tensor,
        sample_rate: int,
        effect_name: str,
        effect_params: List[str],
        duration: Tuple[float, float],
    ):
        if not duration:
            # if duration is None, apply for the entire signal
            start, end = 0, None
        else:
            duration = map(lambda x: int(x * sample_rate), duration)
            start, end = tuple(duration)
        effects = [[effect_name, *effect_params]]
        audio[:, start:end] = torchaudio.sox_effects.apply_effects_tensor(
            audio[:, start:end], sample_rate, effects
        )[0]
        return audio

    def apply(
        self, audio: torch.Tensor, sample_rate: int, channels_first=False
    ) -> torch.Tensor:
        if not channels_first:
            audio = audio.swapaxes(0, 1)

        for audio_effect in self.effects:
            audio = self._apply_interval(
                audio,
                sample_rate,
                audio_effect.effect_name,
                audio_effect.effect_params.values(),
                audio_effect.duration,
            )

        if not channels_first:
            audio = audio.swapaxes(0, 1)
        return audio

    def clear(self) -> None:
        self.effects = []


def augment_signal(signal: torch.Tensor, augmentations: List[BaseAugment]):
    affect = AudioEffectHelper()
    for augmentation in augmentations:
        if augmentation.augment_type == Augmentation.Volume:
            affect.vol(
                str(augmentation.gain),
                (augmentation.start_time, augmentation.end_time),
            )
        elif augmentation.augment_type == Augmentation.Copy:
            pass
    signal = affect.apply(signal)
    return signal
