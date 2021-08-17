from enum import Enum
from pydantic import BaseModel, Field


class Augmentation(str, Enum):
    Base: str = "Base"
    Volume: str = "Volume"
    Copy: str = "Copy"
    Reverb: str = "Reverb"


class BaseAugment(BaseModel):
    augment_type: Augmentation = Field(
        Augmentation.Base, description="Augment Type"
    )
    signal_id: str = Field(..., description="Separated Signal ID")
    signal_stem: str = Field(
        ..., example="Vocals", description="Name of separated stem"
    )
    start_time: int = Field(
        ..., example=10, description="Start time of augment"
    )
    end_time: int = Field(..., example=60, description="End time of augment")


class Volume(BaseAugment):
    augment_type: Augmentation = Field(
        Augmentation.Volume, description="Augment Type"
    )
    gain: float = Field(
        ...,
        example=0.1,
        description="Volume ratio, negative indicates inversion of signal",
    )


class Copy(BaseAugment):
    augment_type: Augmentation = Field(
        Augmentation.Copy, description="Augment Type"
    )
    copy_start_time: int = Field(
        ..., example=10, description="New start time of augment"
    )
    copy_end_time: int = Field(
        ..., example=60, description="New end time of augment"
    )


class Reverb(BaseAugment):
    augment_type: Augmentation = Field(
        Augmentation.Reverb, description="Augmentation Type"
    )
    reverberance: int = Field(
        ..., example=50, description="Percentage of reverberation"
    )
