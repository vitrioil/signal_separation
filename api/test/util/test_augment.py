import numpy as np


from api.utils.augment import AudioEffectHelper, to_tensor


def test_vol():
    ones = np.ones((1000, 1), dtype=np.float32)

    affect = AudioEffectHelper()
    affect.vol("0", (0, 1))
    affect.vol("0.5", (999, 1000))
    augmented_ones = affect.apply(to_tensor(ones), 1)

    assert augmented_ones.shape == (1000, 1)
    assert augmented_ones[0, :] == 0
    assert augmented_ones[-1, :] == 0.5

    ones = np.ones((1, 1000), dtype=np.float32)

    affect = AudioEffectHelper()
    affect.vol("0", (0, 1))
    affect.vol("0.5", (999, 1000))
    augmented_ones = affect.apply(to_tensor(ones), 1, channels_first=True)

    assert augmented_ones.shape == (1, 1000)
    assert augmented_ones[:, 0] == 0
    assert augmented_ones[:, -1] == 0.5
