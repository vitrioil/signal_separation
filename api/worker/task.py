import asyncio

from api.db import get_database, connect_to_mongo
from api.worker import app
from api.schemas import Signal, SeparatedSignal
from api.utils.signal import split_audio
from api.services import (
    create_stem,
    read_signal_file,
    save_stem_file,
    update_signal,
    get_stem_id,
)
from api.separator import SignalType, SpleeterSeparator
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def get_separator(signal_type: SignalType, stems: int):
    if signal_type == SignalType.Music:
        separator = SpleeterSeparator(stems=stems)
    return separator


@app.task(bind=True)
def separate(self, signal: dict, stems: int = 2):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_separate(self, signal, stems))


async def _separate(self, signal: dict, stems: int):
    # TODO: separate out db dependency
    await connect_to_mongo()
    db = await get_database()
    self.update_state(state="PROGRESS", meta={"state": "init"})

    signal = Signal(**signal)
    signal_type = signal.signal_metadata.signal_type
    separator = get_separator(signal_type, stems)

    # TODO: use generators, mem expensive
    stream = await read_signal_file(
        db, signal.signal_metadata.filename, stream=False
    )
    self.update_state(state="PROGRESS", meta={"state": "start"})

    separated_signals = split_audio(
        separator, stream, signal.signal_metadata.extension, signal_type,
    )
    self.update_state(state="PROGRESS", meta={"state": "separated"})

    separated_stems = []
    separated_stem_id = []
    for stem_name, separate_signal in separated_signals.items():
        stem_file_id = get_stem_id(stem_name, signal.signal_id)
        stem_id = await save_stem_file(
            db,
            stem_file_id,
            separate_signal,
            signal.signal_metadata.sample_rate,
        )

        separated_stems.append(stem_name)
        separated_stem_id.append(stem_id)
        stem = SeparatedSignal(
            signal_id=stem_id,
            signal_metadata=signal.signal_metadata,
            stem_name=stem_name,
        )

        await create_stem(db, stem)
    self.update_state(state="PROGRESS", meta={"state": "storing"})

    # store signal stem ids in original signal
    await update_signal(
        db,
        signal.signal_id,
        separated_stems=separated_stems,
        separated_stem_id=separated_stem_id,
    )
    self.update_state(state="PROGRESS", meta={"state": "complete"})
