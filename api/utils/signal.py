from typing import Dict, Tuple
from pathlib import Path
from tempfile import TemporaryFile

import numpy as np
from pydub import AudioSegment
from fastapi import UploadFile

from api.schemas import SignalMetadata
from api.separator import Separator, SignalType


def pydub_to_np(audio: AudioSegment) -> Tuple[np.ndarray, int]:
    array = np.array(audio.get_array_of_samples(), dtype=np.float32).reshape(
        (-1, audio.channels)
    ).T / (1 << (8 * audio.sample_width))
    signal = np.transpose(array, (1, 0))
    return signal


def read_audio(stream: bytes, extension: str) -> np.ndarray:
    with TemporaryFile() as temp_file:
        temp_file.write(stream)
        temp_file.seek(0)
        signal = AudioSegment.from_file(temp_file)

    signal = pydub_to_np(signal)
    return signal


def split_audio(
    separator: Separator,
    stream: bytes,
    extension: str,
    signal_type: SignalType,
) -> Dict[str, np.ndarray]:
    signal = read_audio(stream, extension)
    stems = separator.separate(signal)
    return stems


def process_signal(
    signal_file: UploadFile,
    signal_type: SignalType,
    project_name="",
    segment=False,
    array=False,
) -> SignalMetadata:
    filename, extension, audio_segment = file_to_segment(signal_file)

    signal_metadata = SignalMetadata(
        extension=extension,
        sample_rate=audio_segment.frame_rate,
        duration=audio_segment.duration_seconds,
        channels=audio_segment.channels,
        sample_width=audio_segment.sample_width,
        signal_type=signal_type,
        filename=filename,
        projectname=project_name,
    )
    if segment:
        return signal_metadata, audio_segment
    if array:
        return signal_metadata, pydub_to_np(audio_segment)
    return signal_metadata


def file_to_segment(signal_file: UploadFile):
    filename = signal_file.filename
    extension = Path(filename).suffix.replace(".", "")
    audio_segment = AudioSegment.from_file(signal_file.file)
    return filename, extension, audio_segment
