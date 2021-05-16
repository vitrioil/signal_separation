from tempfile import NamedTemporaryFile

from api.schemas import Signal, SignalState
from api.test.constants import (
    TEST_SIGNAL_ID,
    TEST_DURATION_SECONDS,
    TEST_STEMS,
)


def test_get_signal(signal, client, cleanup_db):
    response = client.get("/signal")

    data = response.json()
    print(data)
    assert response.status_code == 200
    assert len(data) == 1
    signal_actual = data[0]
    assert signal_actual["signal"] == Signal(**signal.dict()).dict()


def test_get_stem_state(signal_state, client, cleanup_db):
    response = client.get(f"/signal/state/{TEST_SIGNAL_ID}")

    data = response.json()
    assert response.status_code == 200
    signal_state_actual = data
    assert signal_state_actual == SignalState(**signal_state.dict()).dict()

    response = client.get("/signal/state/0")

    data = response.json()
    assert response.status_code == 404


def test_post_signal(signal_file_name, client, celery_app, cleanup_db):
    response = client.post(
        "/signal/Music",
        files={
            "signal_file": (
                "filename",
                open(signal_file_name, "rb"),
                "audio/mpeg",
            )
        },
    )

    data = response.json()
    assert response.status_code == 201
    signal_actual = data["signal"]
    assert (
        signal_actual["signal_metadata"]["duration"] == TEST_DURATION_SECONDS
    )

    response = client.post("/signal/Music")
    assert response.status_code == 422

    with NamedTemporaryFile("rb") as file:
        response = client.post(
            "/signal/Music",
            files={"signal_file": ("filename", file, "audio/mpeg",)},
        )
    assert response.status_code == 400


def test_patch_signal(signal, signal_file_name, client, cleanup_db):
    stem_name = "new_stem"
    response = client.patch(
        f"/signal/invalid/{stem_name}",
        files={
            "signal_file": (
                "filename",
                open(signal_file_name, "rb"),
                "audio/mpeg",
            )
        },
    )
    data = response.json()
    assert response.status_code == 404

    response = client.patch(
        f"/signal/{TEST_SIGNAL_ID}/{stem_name}",
        files={
            "signal_file": (
                "filename",
                open(signal_file_name, "rb"),
                "audio/mpeg",
            )
        },
    )
    data = response.json()
    assert response.status_code == 202
    assert data["signal"]["signal_id"] == TEST_SIGNAL_ID
    assert data["signal"]["separated_stems"][-1] == stem_name


def test_delete_stem(generate_stem, client, cleanup_db):
    response = client.delete(f"/signal/{TEST_SIGNAL_ID}/invalid")
    assert response.status_code == 404

    response = client.delete(f"/signal/invalid/{TEST_STEMS[0]}")
    assert response.status_code == 404

    response = client.delete(f"/signal/{TEST_SIGNAL_ID}/{TEST_STEMS[0]}")
    data = response.json()
    assert response.status_code == 202
    assert data["stem_name"] == TEST_STEMS[0]
    assert data["deleted"]

    response = client.get(f"/signal/stem/{TEST_SIGNAL_ID}/{TEST_STEMS[0]}")
    assert response.status_code == 404

    response = client.get(f"/signal/stem/{TEST_SIGNAL_ID}/{TEST_STEMS[1]}")
    assert response.status_code == 200


def test_delete_signal(signal, client, cleanup_db):
    # TODO
    response = client.delete("/signal/0")
    assert response.status_code == 404

    response = client.delete(f"/signal/{TEST_SIGNAL_ID}")
    assert response.status_code == 404


def test_get_stem(generate_stem, client):
    response = client.get(f"/signal/stem/{TEST_SIGNAL_ID}/invalid")
    assert response.status_code == 404

    response = client.get(f"/signal/stem/Invalid/{TEST_STEMS[0]}")
    assert response.status_code == 404

    response = client.get(f"/signal/stem/{TEST_SIGNAL_ID}/{TEST_STEMS[0]}")
    data = response.content
    assert response.status_code == 200
    assert data
