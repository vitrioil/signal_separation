from typing import List
from enum import Enum
from pydantic import BaseModel, Field, BaseConfig

from api.schemas import DBModelMixin


class SignalType(str, Enum):
    Speech: str = "Speech"
    Music: str = "Music"


class SignalMetadata(BaseModel):
    extension: str = Field(..., example="mp3", description="Extension of signal file")
    sample_rate: int = Field(..., example=42_000, description="Sample rate of signal")
    length: int = Field(..., example=60, description="Length of signal in seconds")
    channels: int = Field(..., example=2, description="Number of channels of signal")
    signal_type: SignalType = Field(
        ..., example=SignalType.Music, description="Type of Signal"
    )


class Signal(BaseModel):
    signal_metadata: SignalMetadata = Field(..., description="Signal Metadata")
    signal_id: str = Field(..., description="Signal ID")
    separated_stem_id: List[str] = Field([], description="Signal ID of separated stems")


class SignalInResponse(BaseModel):
    signal: Signal


class SignalInCreate(Signal):
    pass


class SignalInDB(DBModelMixin, Signal):
    pass


class SeparatedSignal(Signal):
    signal_id: str = Field(..., description="Signal ID")
    stem_name: str = Field(..., example="Vocals", description="Name of separated stem")
    signal: Signal = Field(..., description="Separated signal")
