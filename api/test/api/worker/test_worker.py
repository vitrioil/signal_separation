import numpy as np
import pytest
from unittest.mock import patch

from api.test.constants import TEST_SIGNAL_FILE_NAME, TEST_USERNAME
from api.services import read_one_signal
from api.separator import Separator as ABCSeparator


class TestSeparator(ABCSeparator):
    def __init__(self, stems: int):
        self.stems = stems

    def separate(self, audio: np.ndarray):
        predictions = {f"{i}": audio.copy() for i in range(self.stems)}
        return predictions


@pytest.fixture
def separator_mock(mocker, stems):
    mocker.patch(
        "api.worker.task.get_separator", return_value=TestSeparator(stems)
    )


@pytest.fixture
def celery_state_update_mock():
    class MockUpdate:
        def update_state(_, state, meta):
            pass

    return MockUpdate()


@pytest.fixture
def signal_celery_setup(signal_file_name, client, celery_app):
    response = client.post(
        "/signal/Music",
        files={
            "signal_file": (
                TEST_SIGNAL_FILE_NAME,
                open(signal_file_name, "rb"),
                "audio/mpeg",
            )
        },
    )

    response = client.get("/signal")
    signal = response.json()[0]["signal"]
    return signal


@patch("api.worker.task.perform_separation")
def test_separate(separate_mock):
    from api.worker import separate

    separate.apply(args=(None, None))
    assert separate_mock.called


@pytest.mark.parametrize("stems", (2, 4, 5))
@pytest.mark.asyncio
async def test_perform_separation(
    db_client,
    client,
    user,
    signal_celery_setup,
    stems,
    celery_state_update_mock,
    separator_mock,
    cleanup_db,
):
    from api.worker import perform_separation

    await perform_separation(
        celery_state_update_mock,
        signal_celery_setup,
        user.dict(),
        stems,
        db_client,
    )
    signal_actual = await read_one_signal(
        db_client, signal_celery_setup["signal_id"], TEST_USERNAME
    )
    assert len(signal_actual.separated_stems) == stems
