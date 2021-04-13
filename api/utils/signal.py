from io import BytesIO
import numpy as np
from pydub import AudioSegment

from api.schemas import SignalType
from api.separator import separate


def pydub_to_np(audio: AudioSegment) -> (np.ndarray, int):
    """Converts pydub audio segment into float32 np array of shape [channels, duration_in_seconds*sample_rate],
    where each value is in range [-1.0, 1.0]. Returns tuple (audio_np_array, sample_rate)"""
    # get_array_of_samples returns the data in format:
    # [sample_1_channel_1, sample_1_channel_2, sample_2_channel_1, sample_2_channel_2, ....]
    # where samples are integers of sample_width bytes.
    return (
        np.array(audio.get_array_of_samples(), dtype=np.float32)
        .reshape((-1, audio.channels))
        .T
        / (1 << (8 * audio.sample_width)),
        audio.frame_rate,
    )


class AudioExtension:
    def read(stream: bytes):
        signal = AudioSegment.from_file_using_temporary_files(BytesIO(stream), format="wav")#, sample_width=2, frame_rate=44_100, channels=2)
        signal, _ = pydub_to_np(signal)
        signal = np.transpose(signal, (1, 0))
        return signal

    def read_mp3(stream: bytes):
        pass

    def read_wav(stream: bytes):
        pass

    def read_flac(stream: bytes):
        pass

    def read_m4a(stream: bytes):
        pass


def read_audio(stream: bytes, extension: str):
    return AudioExtension.read(stream)

    # if extension.endswith("mp3"):
    #     AudioExtension.read_mp3(stream)
    # elif extension.endswith("wav"):
    #     AudioExtension.read_wav(stream)
    # elif extension.endswith("wav"):
    #     AudioExtension.read_wav(stream)
    # elif extension.endswith("flac"):
    #     AudioExtension.read_flac(stream)
    # else:
    #     return


def audio_to_file_like(signal: np.ndarray):
    audio_segment = AudioSegment(
        signal.tobytes(),
        frame_rate=44_100,
        sample_width=signal.dtype.itemsize,
        channels=2,
    )
    buffer = BytesIO()
    audio_segment.export(buffer, format="wav")
    buffer.seek(0)
    return buffer


def split_audio(stream: bytes, extension: str, signal_type: SignalType):
    signal = read_audio(stream, extension)
    stems = separate(signal, signal_type)
    stems = {k: audio_to_file_like(v) for k, v in stems.items()}
    return stems
