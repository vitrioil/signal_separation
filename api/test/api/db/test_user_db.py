import pytest

from api.schemas import UserInCreate
from api.services import create_user, get_user


pytestmark = pytest.mark.asyncio


async def test_get_user(db_client, user_db, cleanup_db):
    user = await get_user(db_client, user_db.username)
    assert user.username == user_db.username

    user = await get_user(db_client, "invalid")
    assert not user


async def test_create_user(db_client, user, user_db, cleanup_db):
    user_in_db = await get_user(db_client, user.username)
    user_created = await create_user(
        db_client, user, user_in_db.hashed_password
    )
    assert not user_created

    user.password = "test2"
    user_created = await create_user(
        db_client, user, user_in_db.hashed_password
    )
    assert not user_created

    user.username = "test2"
    user_created = await create_user(
        db_client, user, user_in_db.hashed_password
    )
    assert user_created.username == user.username
