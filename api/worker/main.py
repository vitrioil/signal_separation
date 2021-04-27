from enum import Enum
from celery import Celery


class TaskState(str, Enum):
    Start: str = "Start"
    Separating: str = "Separating"
    Aborted: str = "Aborted"
    Separated: str = "Separated"
    Saving: str = "Saving"
    Complete: str = "Complete"


app = Celery("worker", broker="pyamqp://guest@localhost//", backend="rpc://")
