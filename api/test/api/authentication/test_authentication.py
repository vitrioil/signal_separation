import pytest
from fastapi import HTTPException

from api.routers.authentication import create_access_token
from api.dependencies import get_current_user


@pytest.mark.asyncio
async def test_wrong_token(db_client, user_db):
    with pytest.raises(HTTPException):
        await get_current_user("", db_client)

    token = create_access_token({"sub": "invalid"})
    with pytest.raises(HTTPException):
        await get_current_user(token, db_client)

    token = create_access_token({})
    with pytest.raises(HTTPException):
        await get_current_user(token, db_client)


@pytest.mark.asyncio
async def test_token(db_client, user_db):
    token = create_access_token({"sub": user_db.username})
    user = await get_current_user(token, db_client)
    assert user.username == user_db.username

    token = create_access_token({"su": user_db.username})
    with pytest.raises(HTTPException):
        user = await get_current_user(token, db_client)
