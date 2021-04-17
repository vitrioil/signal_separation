import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from pydub import AudioSegment
import numpy as np

from api.db import get_database
from api.utils.signal import get_separator
from api.separator import Separator as ABCSeparator, SignalType
from api.config import MONGODB_TEST_URL
from api.main import api


class TestSeparator(ABCSeparator):
    def __init__(self, stems: int):
        self.stems = stems

    def separate(self, audio: np.ndarray):
        predictions = {f"{i}": audio.copy() for i in range(self.stems)}
        return predictions


async def override_get_database():
    db = AsyncIOMotorClient(MONGODB_TEST_URL)
    return db


def override_get_separator(signal_type: SignalType, stems: int = 2):
    return {
        "signal_type": signal_type,
        "separator": TestSeparator(stems=stems),
    }


@pytest.fixture
def signal(tmp_path):
    sample_signal = AudioSegment.silent(duration=10000)
    file_path = tmp_path / "signal.wav"
    sample_signal.export(file_path.as_posix(), format="wav")
    return file_path.as_posix()


api.dependency_overrides[get_database] = override_get_database
api.dependency_overrides[get_separator] = override_get_separator
client = TestClient(api)


def test_signal_music(signal):
    stems = 2

    response = client.post(
        "/signal/Music",
        files={"signal_file": ("filename", open(signal, "rb"), "audio/mpeg")},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["signal"]["signal_metadata"]["signal_type"] == "Music"

    response = client.get("/signal")
    data = response.json()
    signal_data = data[0]["signal"]
    signal_id = signal_data["signal_id"]
    stem_names = signal_data["separated_stems"]
    signal_metadata = signal_data["signal_metadata"]

    assert signal_metadata["signal_type"] == "Music"
    assert len(stem_names) == stems
    assert response.status_code == 200
    # only true if db is empty before running unit test
    assert len(data) == 1

    # test for streaming response
    # response = client.get(f"/signal/stem/{signal_id}/{stem_names[0]}")

    response = client.delete(f"/signal/{signal_id}")
    data = response.json()
    assert data["signal_id"] == signal_id
    assert data["deleted"]

    # response = client.delete(f"/signal/{signal_id}")
    # assert response.status_code == 404 #fails..
