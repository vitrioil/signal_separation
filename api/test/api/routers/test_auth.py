from api.test.constants import TEST_USERNAME, TEST_PASSWORD, TEST_EMAIL


def test_register_user(user_db, client, cleanup_db):
    response = client.post("/user/register", json=user_db.dict())
    assert response.status_code == 400

    user_db.username = "test2"
    response = client.post("/user/register", json=user_db.dict())

    assert response.status_code == 201
    user = response.json()["user"]
    assert user["username"] == "test2"
    assert user["email"] == TEST_EMAIL


def test_token(user_db, client, cleanup_db):
    response = client.post(
        "/token", data={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401

    response = client.post(
        "/token", data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    data = response.json()
    assert response.status_code == 200
    assert data["token_type"] == "bearer"
    assert data["access_token"]
