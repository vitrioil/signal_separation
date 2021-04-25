import orjson
from typing import List
from pydantic import BaseModel, Field

from api.schemas import DBModelMixin
from api.separator import SignalType


class SignalMetadata(BaseModel):
    extension: str = Field(
        ..., example="mp3", description="Extension of signal file"
    )
    sample_rate: int = Field(
        ..., example=42_000, description="Sample rate of signal"
    )
    duration: int = Field(
        ..., example=60, description="Duration of signal in seconds"
    )
    channels: int = Field(
        ..., example=2, description="Number of channels of signal"
    )
    sample_width: int = Field(..., example=2, description="Bytes per sample")
    signal_type: SignalType = Field(
        ..., example=SignalType.Music, description="Type of Signal"
    )
    filename: str = Field(..., example="Song", description="Name of file")


class SignalBase(BaseModel):
    signal_metadata: SignalMetadata = Field(..., description="Signal Metadata")
    signal_id: str = Field(..., description="Signal ID")


class Signal(SignalBase):
    separated_stems: List[str] = Field([], description="Name of stems")

    class Config:
        json_loads = orjson.loads


class SignalInCreate(Signal):
    pass


class SignalInDB(DBModelMixin, Signal):
    separated_stem_id: List[str] = Field([], description="Signal ID of Stems")


class SignalInResponse(BaseModel):
    signal: Signal


class SeparatedSignal(SignalBase):
    stem_name: str = Field(
        ..., example="Vocals", description="Name of separated stem"
    )


class SeparatedSignalInDB(DBModelMixin, SeparatedSignal):
    pass


class SignalState(BaseModel):
    signal_id: str = Field(..., description="Signal ID")
    signal_state: str = Field(..., description="Signal State")


class SignalStateInDB(DBModelMixin, SignalState):
    pass
