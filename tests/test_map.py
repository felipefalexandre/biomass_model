import numpy as np

from biomass_model.inference.map import _block_mean


def test_block_mean_ignores_nan_and_edges():
    arr = np.array([
        [1.0, 3.0, 5.0, 7.0],
        [1.0, 3.0, 5.0, 7.0],
        [2.0, 4.0, 6.0, 8.0],
        [2.0, 4.0, 6.0, 8.0],
    ], dtype="float32")
    out = _block_mean(arr, nb=2, block=2)
    assert np.allclose(out, [[2.0, 6.0], [3.0, 7.0]])

    arr[0, 0] = np.nan
    out = _block_mean(arr, nb=2, block=2)
    assert np.isclose(out[0, 0], (3.0 + 1.0 + 1.0 + 3.0) / 4)
