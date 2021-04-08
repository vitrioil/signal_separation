from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from api.db import get_database
from api.config import MONGODB_TEST_URL, signal_collection_name
from api.main import api


async def override_get_database():
    db = AsyncIOMotorClient(MONGODB_TEST_URL)
    # await db.get_default_database().drop_collection(signal_collection_name)
    return db


api.dependency_overrides[get_database] = override_get_database
client = TestClient(api)


def test_signal():
    response = client.post("/signal/Speech", json={})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["signal"]["signal_metadata"]["signal_type"] == "Speech"

    response = client.get("/signal")
    data = response.json()
    assert data[0]["signal_metadata"]["signal_type"] == "Speech"
    assert response.status_code == 200

    response = client.delete("/signal/TEST", json={})
    data = response.json()
    assert data["deleted"]

    response = client.delete("/signal/TEST", json={})
    data = response.json()
    assert not data["deleted"]
