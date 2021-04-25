import pytest
import asyncio
from tempfile import NamedTemporaryFile
from fastapi.testclient import TestClient

from pydub import AudioSegment
import numpy as np

from api.db import get_database
from api.separator import Separator as ABCSeparator, SignalType
from api.config import (
    signal_collection_name,
    stem_collection_name,
    grid_bucket_name,
)
from api.main import api
from ..conftest import override_get_database


class TestSeparator(ABCSeparator):
    def __init__(self, stems: int):
        self.stems = stems

    def separate(self, audio: np.ndarray):
        predictions = {f"{i}": audio.copy() for i in range(self.stems)}
        return predictions


async def _override_get_database():
    return override_get_database()


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


# set the event loop for cleanup
@pytest.fixture
def loop():
    return asyncio.get_event_loop()


# cleanup after running unit test
@pytest.fixture
async def cleanup_db(loop):
    yield
    db = await override_get_database()
    await db.get_default_database().drop_collection(stem_collection_name)
    await db.get_default_database().drop_collection(signal_collection_name)
    await db.get_default_database().drop_collection(
        f"{grid_bucket_name}.files"
    )
    await db.get_default_database().drop_collection(
        f"{grid_bucket_name}.chunks"
    )


api.dependency_overrides[get_database] = _override_get_database
# api.dependency_overrides[get_separator] = override_get_separator
client = TestClient(api)


def test_signal_music(signal, cleanup_db):
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

    response = client.get(f"/signal/stem/{signal_id}/{stem_names[0]}")
    data = response.content
    with NamedTemporaryFile() as temp_file:
        temp_file.write(data)
        temp_file.seek(0)
        signal = AudioSegment.from_file(temp_file)
    assert signal.duration_seconds == 10
    assert response.status_code == 200

    response = client.delete(f"/signal/{signal_id}")
    data = response.json()
    assert data["signal_id"] == signal_id
    assert data["deleted"]
    assert response.status_code == 202

    response = client.delete(f"/signal/{signal_id}")
    assert response.status_code == 404
