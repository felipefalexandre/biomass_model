import numpy as np

from biomass_model.applicability import fit_aoa, score_aoa


def test_aoa_flags_far_point():
    rng = np.random.default_rng(42)
    train = rng.normal(0, 1, size=(50, 3))
    aoa = fit_aoa(train, quantile=0.95)
    near = rng.normal(0, 1, size=(5, 3))
    far = np.array([[10.0, 10.0, 10.0]])
    d_near, inside_near = score_aoa(aoa, near)
    d_far, inside_far = score_aoa(aoa, far)
    assert inside_near.mean() >= 0.6
    assert inside_far[0] is np.bool_(False) or not inside_far[0]
    assert d_far[0] > aoa["threshold"]
