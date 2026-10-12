"""
Tests for the viability surrogate and group-statistics modules.

The viability test generates its OWN synthetic spheroid image in a temporary
file, so the suite is fully self-contained and portable across machines
(no dependency on any developer's absolute file path).
"""
import os
import tempfile
import numpy as np
import cv2

from spheroidkit.analysis.stats import compare_two, compare_many, holm_bonferroni
from spheroidkit import analyze_image


def _make_synthetic_spheroid(path, size=600):
    """Write a synthetic phase/brightfield-like spheroid image to `path`.

    A dark, granular (textured) disc on a light background — enough structure
    for the texture-based segmentation to find a single central object.
    """
    rng = np.random.default_rng(0)
    img = np.full((size, size, 3), 220, np.uint8)
    noise = rng.integers(-8, 8, (size, size, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    yy, xx = np.mgrid[0:size, 0:size]
    cx = cy = size // 2
    r = size // 4
    disc = (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2
    tex = rng.integers(-35, 35, (size, size), dtype=np.int16)
    for c in range(3):
        ch = img[:, :, c].astype(np.int16)
        ch[disc] = np.clip(140 + tex[disc], 0, 255)
        img[:, :, c] = ch.astype(np.uint8)
    cv2.imwrite(path, img)


def test_two_group_detects_difference():
    r = compare_two([100, 102, 98, 101], [60, 58, 62, 59], parametric=False)
    assert r.significant
    assert r.test == "Mann-Whitney U"


def test_no_false_positive_identical():
    r = compare_two([100, 101, 99], [100, 101, 99], parametric=False)
    assert not r.significant


def test_multi_group_and_holm():
    mr = compare_many([[10, 11, 9], [20, 21, 19], [40, 39, 41]], parametric=False)
    assert mr.n_groups == 3
    adj, rej = holm_bonferroni([0.01, 0.04, 0.005])
    assert all(a >= p for a, p in zip(adj, [0.01, 0.04, 0.005]))


def test_viability_runs_and_flags_surrogate():
    """Self-contained: generate an image, analyze it, check the surrogate flag."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "synthetic_spheroid.png")
        _make_synthetic_spheroid(path)
        r = analyze_image(path, with_viability=True)
        assert r.viability is not None
        assert r.viability.is_surrogate is True
        assert 0 <= r.viability.index <= 1
