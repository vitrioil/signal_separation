import pytest
import numpy as np

# get test database (conftest.py)
from api.worker import TaskState

# test methods import
from api.services import (
    read_one_signal,
    create_signal,
    update_signal,
    read_signal,
    remove_signal,
    get_signal_state,
    update_signal_state,
    save_signal_file,
    read_signal_file,
    delete_signal_file,
    save_stem_file,
)
from api.test.conftest import _get_signal


pytestmark = pytest.mark.asyncio


async def test_read_one_signal(signal, db_client, cleanup_db):
    signal_actual = await read_one_signal(db_client, signal.signal_id)
    assert signal.signal_id == signal_actual.signal_id

    signal_actual = await read_one_signal(db_client, "99")
    assert not signal_actual


async def test_create_signal(db_client, cleanup_db):
    signal = _get_signal()
    await create_signal(db_client, signal)

    signal_actual = await read_one_signal(db_client, signal.signal_id)
    assert signal.signal_id == signal_actual.signal_id


async def test_update_signal(signal, db_client, cleanup_db):
    update_fields = {"separated_stems": ["one", "two"]}
    await update_signal(db_client, signal.signal_id, **update_fields)

    signal_actual = await read_one_signal(db_client, signal.signal_id)
    assert signal_actual.separated_stems == update_fields["separated_stems"]

    signal_actual = await read_one_signal(db_client, "99")
    assert not signal_actual


async def test_read_all_signals(db_client, cleanup_db):
    signal = _get_signal()
    await create_signal(db_client, signal)

    signal.signal_id = "2"
    await create_signal(db_client, signal)

    signals = await read_signal(db_client)
    assert len(signals) == 2


async def test_delete_signal(signal, db_client, cleanup_db):
    deleted_count = await remove_signal(db_client, signal.signal_id)
    assert deleted_count == 1

    deleted_count = await remove_signal(db_client, signal.signal_id)
    assert not deleted_count


async def test_get_signal_state(signal_state, db_client, cleanup_db):
    signal_state_actual = await get_signal_state(
        db_client, signal_state.signal_id
    )
    assert signal_state_actual == signal_state


async def test_update_signal_state(signal_state, db_client, cleanup_db):
    signal_state.signal_state = TaskState.Complete
    signal_state_updated = await update_signal_state(db_client, signal_state)
    assert signal_state_updated.signal_state == TaskState.Complete


async def test_signal_file(db_client, signal_file, cleanup_db):
    name = signal_file.filename
    file_id = await save_signal_file(db_client, signal_file)
    content = await read_signal_file(db_client, name, stream=False)
    assert content

    content = await read_signal_file(db_client, "INVALID.wav", stream=False)
    assert not content

    await delete_signal_file(db_client, file_id)
    content = await read_signal_file(db_client, name, stream=False)
    assert not content


@pytest.mark.parametrize(
    "sr, duration, channels",
    ((44_100, 10, 2), (22_050, 20, 1), (11_025, 5, 2)),
)
async def test_stem_file(db_client, cleanup_db, sr, duration, channels):
    def _create_signal(duration, sr, channels):
        return np.zeros((duration * sr, channels))

    stem_id = "test_stem"
    test_stem = _create_signal(duration, sr, channels)
    file_id = await save_stem_file(db_client, stem_id, test_stem, sr)
    content = await read_signal_file(db_client, stem_id, stream=False)
    assert content

    await delete_signal_file(db_client, file_id)
    content = await read_signal_file(db_client, stem_id, stream=False)
    assert not content
