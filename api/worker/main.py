from celery import Celery

app = Celery("worker", broker="pyamqp://guest@localhost//")
