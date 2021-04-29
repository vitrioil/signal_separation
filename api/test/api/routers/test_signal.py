import pytest

from pydub import AudioSegment
import numpy as np

from api.separator import Separator as ABCSeparator, SignalType


class TestSeparator(ABCSeparator):
    def __init__(self, stems: int):
        self.stems = stems

    def separate(self, audio: np.ndarray):
        predictions = {f"{i}": audio.copy() for i in range(self.stems)}
        return predictions


def override_get_separator(signal_type: SignalType, stems: int = 2):
    return {
        "signal_type": signal_type,
        "separator": TestSeparator(stems=stems),
    }


@pytest.fixture
def signal_file(tmp_path):
    sample_signal = AudioSegment.silent(duration=10000)
    file_path = tmp_path / "signal.wav"
    sample_signal.export(file_path.as_posix(), format="wav")
    return file_path.as_posix()


@pytest.mark.asyncio
async def test_get_signal(
    signal, api, client, cleanup_db
):
    response = await client.get("/signal")

    data = response.json()
    print(data)
    assert response.status_code == 200
    assert len(data) == 1
    signal_actual = data[0]
    assert signal_actual.dict() == signal.dict()


# def test_signal_music(signal, cleanup_db):
#     stems = 2

#     response = client.post(
#         "/signal/Music",
#         files={"signal_file": ("filename", open(signal, "rb"),
# "audio/mpeg")},
#     )

#     assert response.status_code == 201, response.text
#     data = response.json()
#     assert data["signal"]["signal_metadata"]["signal_type"] == "Music"

#     response = client.get("/signal")
#     data = response.json()
#     signal_data = data[0]["signal"]
#     signal_id = signal_data["signal_id"]
#     stem_names = signal_data["separated_stems"]
#     signal_metadata = signal_data["signal_metadata"]

#     assert signal_metadata["signal_type"] == "Music"
#     assert len(stem_names) == stems
#     assert response.status_code == 200
#     # only true if db is empty before running unit test
#     assert len(data) == 1

#     response = client.get(f"/signal/stem/{signal_id}/{stem_names[0]}")
#     data = response.content
#     with NamedTemporaryFile() as temp_file:
#         temp_file.write(data)
#         temp_file.seek(0)
#         signal = AudioSegment.from_file(temp_file)
#     assert signal.duration_seconds == 10
#     assert response.status_code == 200

#     response = client.delete(f"/signal/{signal_id}")
#     data = response.json()
#     assert data["signal_id"] == signal_id
#     assert data["deleted"]
#     assert response.status_code == 202

#     response = client.delete(f"/signal/{signal_id}")
#     assert response.status_code == 404
