# import pytest

# from api.schemas import Signal, SignalMetadata, SignalType
# from api.worker import app, separate


# @pytest.fixture(scope="module")
# def celery_app(request):
#     app.conf.update(CELERY_ALWAYS_EAGER=True)


# @pytest.fixture
# def signal():
#     s = Signal(
#         signal_id="1",
#         signal_metadata=SignalMetadata(
#             extension="wav",
#             sample_rate=44_100,
#             duration=10,
#             channels=2,
#             sample_width=2,
#             signal_type=SignalType.Music,
#             filename="test.wav",
#         ),
#     )
#     return s.dict()


# def test_separator_task(celery_app, signal, override_get_database):
#     separate.delay(signal)
