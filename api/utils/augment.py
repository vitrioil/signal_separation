import torch
import torchaudio

from typing import List, Any, Tuple
from dataclasses import dataclass


@dataclass
class AudioEffectParameters:
    effect_name: str
    duration: Tuple[float, float]
    effect_params: List[Any]


class AudioEffectHelper:
    """Helper class for all torchaudio effects.

        Example use:
        >>>affect = AudioEffectHelper()
        >>>affect.vol('0.1').vol('0.2')
        >>>effect = affect.apply(audio_tensor, sample_rate)
    """

    def __init__(self):
        self.effects = []

    def vol(self, gain: str, duration: Tuple[float, float] = None):
        """SoX: Apply an amplification or an attenuation to the audio signal.

            Args:
                gain (str): type of gain could be amplitude / power or dB.
                duration (tuple[float, float]): affected time interval.
                    Keep None to apply for entire signal
        """
        self.effects.append(AudioEffectParameters("vol", duration, [gain]))
        return self

    def _apply_interval(
        self,
        audio: torch.Tensor,
        sample_rate: int,
        duration: Tuple[float, float],
    ):
        if not duration:
            # if duration is None, apply for the entire signal
            start, end = 0, None
        else:
            duration = map(lambda x: int(x * sample_rate), duration)
            start, end = tuple(duration)
        audio[:, start:end] = torchaudio.sox_effects.apply_effects_tensor(
            audio[:, start:end], sample_rate
        )[0]
        return audio

    def apply(
        self, audio: torch.Tensor, sample_rate: int, channels_first=False
    ):
        if not channels_first:
            audio = audio.swapaxes(0, 1)

        for audio_effect in self.effects:
            audio = self._apply_interval(
                audio, sample_rate, audio_effect.duration
            )

        if not channels_first:
            audio = audio.swapaxes(0, 1)
        return audio

    def clear(self):
        self.effects = []
