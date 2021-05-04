import pytest
import asyncio
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient
from pydub import AudioSegment

from api.db import db
from api.db import get_database
from api.config import (
    MONGODB_TEST_URL,
    signal_collection_name,
    stem_collection_name,
    signal_state_collection_name,
    grid_bucket_name,
)
from api.separator import SignalType
from api.schemas import SignalInDB, SignalMetadata, SignalState
from api.test.constants import (
    TEST_SIGNAL_ID,
    TEST_SIGNAL_STATE,
    TEST_SIGNAL_FILE_NAME,
    TEST_DURATION_SECONDS,
    TEST_STEMS,
)


async def _db_client():
    db.client = AsyncIOMotorClient(MONGODB_TEST_URL)
    return db.client


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_client(event_loop):
    return await _db_client()


# cleanup after running unit test
@pytest.fixture
async def cleanup_db(db_client):
    yield
    db = db_client
    await db.get_default_database().drop_collection(stem_collection_name)
    await db.get_default_database().drop_collection(signal_collection_name)
    await db.get_default_database().drop_collection(
        signal_state_collection_name
    )
    await db.get_default_database().drop_collection(
        f"{grid_bucket_name}.files"
    )
    await db.get_default_database().drop_collection(
        f"{grid_bucket_name}.chunks"
    )


def _get_signal():
    _signal = SignalInDB(
        signal_metadata=SignalMetadata(
            extension="wav",
            sample_rate=44_100,
            duration=10,
            channels=2,
            sample_width=2,
            signal_type=SignalType.Music,
            filename="test.wav",
        ),
        signal_id=TEST_SIGNAL_ID,
    )
    return _signal


@pytest.fixture
async def signal(db_client):
    signal = _get_signal()
    await db_client.get_default_database().get_collection(
        signal_collection_name
    ).insert_one(signal.dict())
    return signal


@pytest.fixture
async def signal_state(db_client):
    signal_state = SignalState(
        signal_id=TEST_SIGNAL_ID, signal_state=TEST_SIGNAL_STATE
    )
    await db_client.get_default_database().get_collection(
        signal_state_collection_name
    ).insert_one(signal_state.dict())
    return signal_state


@pytest.fixture
def signal_file_name(tmp_path):
    sample_signal = AudioSegment.silent(duration=TEST_DURATION_SECONDS * 1000)
    file_path = tmp_path / TEST_SIGNAL_FILE_NAME
    sample_signal.export(file_path.as_posix(), format="wav")
    return file_path.as_posix()


@pytest.fixture
def signal_file(signal_file_name):
    class Wrapper:
        def __init__(self, obj, filename):
            self.file = obj
            self.filename = filename
            self.content_type = "audio/mpeg"

    with open(signal_file_name, "rb") as f:
        yield Wrapper(f, signal_file_name)


@pytest.fixture
async def generate_stem(signal, signal_file, db_client):
    from api.services import save_stem_file, update_signal, get_stem_id

    sr = 44_100
    test_stem = np.zeros((sr * 10, 2))
    separated_id = []
    for stem_name in TEST_STEMS:
        stem_id = get_stem_id(stem_name, signal.signal_id)
        file_id = await save_stem_file(db_client, stem_id, test_stem, sr)
        separated_id.append(file_id)

    await update_signal(
        db_client,
        signal.signal_id,
        separated_stems=TEST_STEMS,
        separated_stem_id=separated_id,
    )


@pytest.mark.asyncio
@pytest.fixture
async def api():
    from api.main import api as _api

    _api.dependency_overrides[get_database] = _db_client

    return _api


@pytest.fixture
async def initialized_app(api):
    async with LifespanManager(api):
        yield api


@pytest.fixture
async def client(initialized_app):
    # async with AsyncClient(
    #     app=initialized_app, base_url="http://testserver",
    #     headers={"Content-Type": "application/json"},
    # ) as client:
    #     yield client
    return TestClient(initialized_app)


@pytest.fixture
def celery_app():
    from api.worker import app

    app.conf.update(CELERY_ALWAYS_EAGER=True)
    app.conf.update(broker="memory://")
    app.conf.update(backend="cache+memory://")

    return app
