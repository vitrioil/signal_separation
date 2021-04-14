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
    separated_stem_id: List[str] = Field(
        [], description="Signal ID of separated stems"
    )


class SignalInCreate(Signal):
    pass


class SignalInDB(DBModelMixin, Signal):
    pass


class SignalInResponse(BaseModel):
    signal: SignalInDB


class SeparatedSignal(SignalBase):
    stem_name: str = Field(
        ..., example="Vocals", description="Name of separated stem"
    )


class SeparatedSignalInDB(DBModelMixin, SeparatedSignal):
    pass
