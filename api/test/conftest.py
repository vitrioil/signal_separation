import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from api.db import db
from api.config import MONGODB_TEST_URL


@pytest.fixture(scope="session")
def override_get_database():
    db.client = AsyncIOMotorClient(MONGODB_TEST_URL)
    return db.client
