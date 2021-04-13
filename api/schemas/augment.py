from enum import Enum
from pydantic import BaseModel, Field


class AugmentType(str, Enum):
    Volume: str = "Volume"
    Copy: str = "Copy"


class BaseAugment(BaseModel):
    signal_id: str = Field(..., description="Separated Signal ID")
    signal_stem: str = Field(
        ..., example="Vocals", description="Name of separated stem"
    )
    start_time: int = Field(
        ..., example=10, description="Start time of augment"
    )
    end_time: int = Field(..., example=60, description="End time of augment")


class Volume(BaseAugment):
    augment_type: AugmentType = Field(
        AugmentType.Volume, description="Augment Type"
    )
    volume: float = Field(
        ..., example=0.1, description="Percentage change in volume"
    )


class Copy(BaseAugment):
    augment_type: AugmentType = Field(
        AugmentType.Copy, description="Augment Type"
    )
    copy_start_time: int = Field(
        ..., example=10, description="New start time of augment"
    )
    copy_end_time: int = Field(
        ..., example=60, description="New end time of augment"
    )
