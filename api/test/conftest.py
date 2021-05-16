from api.schemas.signal import SignalStateInDB
import pytest
import asyncio
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient
from pydub import AudioSegment

from api.db import db, get_database
from api.dependencies import get_current_user
from api.config import (
    MONGODB_TEST_URL,
    signal_collection_name,
    stem_collection_name,
    signal_state_collection_name,
    user_collection_name,
    grid_bucket_name,
)
from api.separator import SignalType
from api.schemas import (
    SignalInDB,
    SignalMetadata,
    SeparatedSignal,
    UserInCreate,
    UserInDB,
)
from api.test.constants import (
    TEST_SIGNAL_ID,
    TEST_SIGNAL_STATE,
    TEST_SIGNAL_FILE_NAME,
    TEST_DURATION_SECONDS,
    TEST_STEMS,
    TEST_EMAIL,
    TEST_USERNAME,
    TEST_PASSWORD,
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
    await db.get_default_database().drop_collection(user_collection_name)
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
            filename=TEST_SIGNAL_FILE_NAME,
        ),
        signal_id=TEST_SIGNAL_ID,
        username=TEST_USERNAME,
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
    signal_state = SignalStateInDB(
        signal_id=TEST_SIGNAL_ID,
        signal_state=TEST_SIGNAL_STATE,
        username=TEST_USERNAME,
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
    from api.services import (
        save_stem_file,
        update_signal,
        get_stem_id,
        create_stem,
    )

    sr = 44_100
    test_stem = np.zeros((sr * 10, 2))
    separated_id = []
    for stem_name in TEST_STEMS:
        stem_id = get_stem_id(stem_name, TEST_SIGNAL_ID)
        file_id = await save_stem_file(db_client, stem_id, test_stem, sr)
        separated_id.append(file_id)
        stem = SeparatedSignal(
            signal_id=file_id,
            signal_metadata=signal.signal_metadata,
            stem_name=stem_name,
        )

        await create_stem(db_client, stem, TEST_USERNAME)

    await update_signal(
        db_client,
        signal.signal_id,
        TEST_USERNAME,
        separated_stems=TEST_STEMS,
        separated_stem_id=separated_id,
    )


def _user():
    user = UserInCreate(
        username=TEST_USERNAME, email=TEST_EMAIL, password=TEST_PASSWORD
    )
    return user


@pytest.fixture
async def user():
    return _user()


@pytest.fixture
async def user_db(db_client, user):
    from api.routers.authentication import get_password_hash

    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    await db_client.get_default_database().get_collection(
        user_collection_name
    ).insert_one(user_in_db.dict())
    return user


def get_test_current_user():
    return _user()


@pytest.mark.asyncio
@pytest.fixture
async def api():
    from api.main import api as _api

    _api.dependency_overrides[get_database] = _db_client
    _api.dependency_overrides[get_current_user] = get_test_current_user

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
