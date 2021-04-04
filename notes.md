# Model
1. Signal type (Enum)
    1. Music
    2. Speech

2. Signal Metadata
    1. Extension
    2. Sample Rate
    3. Length
    4. Channels
    5. Signal Type (Enum)

3. Signal
    1. Signal Metadata
    2. Signal (binary?)

4. SeparatedSignal
    1. SignalID
    2. StemName
    3. Signal (binary?)

4. Augment type (Enum)
    1. Volume
    2. Copy
    3. Echo
    et cetera

5. BaseAugment
    1. SignalID
    2. Signal Stem
    1. Start Time
    2. End Time

5. Volume(BaseAugment)
    1. AugmentType = AugmentType.Volume
    1. Volume

6. Copy(BaseAugment)
    1. AugmentType = AugmentType.Copy
    1. New Start Time
    2. New End Time

et cetera