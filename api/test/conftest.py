import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from api.db import db
from api.db import get_database
from api.config import (
    MONGODB_TEST_URL,
    signal_collection_name,
    stem_collection_name,
    signal_state_collection_name,
    grid_bucket_name,
)
from api.worker import TaskState
from api.separator import SignalType
from api.schemas import SignalInDB, SignalMetadata, SignalState


def _db_client():
    db.client = AsyncIOMotorClient(MONGODB_TEST_URL)
    return db.client


@pytest.fixture(scope="session")
def db_client():
    return _db_client()


@pytest.yield_fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
        signal_id="1",
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
    signal_state = SignalState(signal_id="1", signal_state=TaskState.Saving)
    await db_client.get_default_database().get_collection(
        signal_state_collection_name
    ).insert_one(signal_state.dict())
    return signal_state


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
async def client(initialized_app, db_client):
    async with AsyncClient(
        app=initialized_app, base_url="http://testserver",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client
