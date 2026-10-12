"""
Regression tests for the v1.1 segmentation change.

Background
----------
v1.1 added two things to `segment()`:

  * `SegmentConfig.opening_radius` (default 4) - a morphological opening applied
    BEFORE the closing step, which severs the thin texture bridges that link the
    corona of shed, disaggregated cells to a drug-treated spheroid's body.
  * `SegmentConfig.edge_tightness` default raised 0.0 -> 0.12, admitting only
    genuinely dense texture.

Both values were fixed on the batch-1 development set (8 calibrated 4x A549
images: 5 control, 3 treated) scored against expert manual ImageJ tracings.
They are FROZEN so a held-out batch can be scored honestly.

These tests exist to stop the frozen behaviour drifting silently. Two layers:

  1. Tests that need no data at all - they run everywhere, including CI.
  2. Pinned per-image areas on the batch-1 images, skipped when those images
     are not on this machine.
"""
import os

import numpy as np
import pytest

from spheroidkit.config import Config, CalibrationConfig, SegmentConfig, DEFAULT
from spheroidkit.core.segment import segment


# --------------------------------------------------------------------------
# Layer 1: no external data required
# --------------------------------------------------------------------------

def test_frozen_defaults():
    """The tuned parameters must not drift.

    If you are changing these, you are re-tuning the segmentation. That is
    allowed, but it invalidates any validation figures produced with the old
    values - update the manuscript and the pinned areas below at the same time.
    """
    assert DEFAULT.segment.edge_tightness == 0.12
    assert DEFAULT.segment.opening_radius == 4
    # Untouched by v1.1 - pinned so the change stays isolated.
    assert DEFAULT.segment.entropy_radius == 9
    assert DEFAULT.segment.closing_radius == 7
    assert DEFAULT.segment.boundary_smooth_sigma == 4.0


def _synthetic_spheroid_with_corona(size=400, core_r=70, seed=0):
    """A dense textured disc surrounded by detached specks.

    Mimics the failure mode: a compact body plus a corona of shed cells that
    the pre-v1.1 pipeline swallowed into the mask.
    """
    rng = np.random.RandomState(seed)
    img = np.full((size, size), 200, np.uint8)          # smooth background
    yy, xx = np.mgrid[:size, :size]
    c = size // 2

    core = (yy - c) ** 2 + (xx - c) ** 2 <= core_r ** 2
    img[core] = rng.randint(0, 255, core.sum())          # high-texture core

    # Detached specks in an annulus well outside the core.
    for _ in range(60):
        ang = rng.uniform(0, 2 * np.pi)
        rad = rng.uniform(core_r + 22, core_r + 75)
        sy = int(c + rad * np.sin(ang))
        sx = int(c + rad * np.cos(ang))
        if 4 <= sy < size - 4 and 4 <= sx < size - 4:
            img[sy - 3:sy + 3, sx - 3:sx + 3] = rng.randint(0, 255, (6, 6))
    return img, core


def test_opening_excludes_detached_corona():
    """With opening on, the mask should track the core, not the corona."""
    img, core = _synthetic_spheroid_with_corona()

    loose = SegmentConfig(opening_radius=0, edge_tightness=0.0,
                          min_object_size=50, min_central_area=100)
    tight = SegmentConfig(opening_radius=4, edge_tightness=0.12,
                          min_object_size=50, min_central_area=100)

    a_loose = segment(img, loose).sum()
    a_tight = segment(img, tight).sum()

    # The tightened pipeline must not be larger than the permissive one.
    assert a_tight <= a_loose
    # And it must stay in the neighbourhood of the true core rather than
    # ballooning out to enclose the speck annulus.
    assert a_tight < 2.5 * core.sum()


def test_opening_radius_zero_restores_legacy_path():
    """opening_radius=0 must skip the opening entirely (pre-v1.1 behaviour)."""
    img, _ = _synthetic_spheroid_with_corona(seed=1)
    cfg_a = SegmentConfig(opening_radius=0, min_object_size=50, min_central_area=100)
    cfg_b = SegmentConfig(opening_radius=0, min_object_size=50, min_central_area=100)
    assert np.array_equal(segment(img, cfg_a), segment(img, cfg_b))


def test_tighter_threshold_never_grows_mask():
    """edge_tightness is monotonic: raising it must not enlarge the mask."""
    img, _ = _synthetic_spheroid_with_corona(seed=2)
    areas = [
        segment(img, SegmentConfig(edge_tightness=t, opening_radius=4,
                                   min_object_size=50, min_central_area=100)).sum()
        for t in (0.0, 0.06, 0.12)
    ]
    assert areas[0] >= areas[1] >= areas[2]


# --------------------------------------------------------------------------
# Layer 2: pinned areas on the batch-1 development images
# --------------------------------------------------------------------------

UM_PER_PX_4X = 0.21949

# Areas in um^2 produced by v1.1 defaults at 0.21949 um/px.
# Regenerate ONLY if you deliberately change the segmentation - and if you do,
# the published agreement figures must be regenerated too.
BATCH1_EXPECTED_AREA_UM2 = {
    "4x-24Hrs.tif": 47606.0,
    "4x-48Hrs (1).tif": 40442.2,
    "4x-48Hrs (2).tif": 40109.2,
    "4x-72hrs (1).tif": 41389.8,
    "4x-72hrs (2).tif": 41405.1,
    "After Drug Adition 4x-72 Hrs (1).bmp": 18242.4,
    "After Drug Adition 4x-72 Hrs (2).bmp": 18133.7,
    "After Drug Adition 4x-72 Hrs (3).bmp": 30660.3,
}


def _image_dir():
    """Locate the batch-1 images, or None if they are not on this machine."""
    env = os.environ.get("SPHEROIDKIT_TEST_IMAGES")
    candidates = [env] if env else []
    candidates += [
        os.path.join(os.path.dirname(__file__), "data", "batch1"),
    ]
    for c in candidates:
        if c and os.path.isdir(c):
            return c
    return None


IMAGE_DIR = _image_dir()

needs_images = pytest.mark.skipif(
    IMAGE_DIR is None,
    reason="batch-1 images not present; set SPHEROIDKIT_TEST_IMAGES to enable",
)


@needs_images
@pytest.mark.parametrize("fname,expected", sorted(BATCH1_EXPECTED_AREA_UM2.items()))
def test_batch1_area_is_stable(fname, expected):
    """Measured area on each development image must not drift by >1%."""
    from spheroidkit import analyze_image

    path = os.path.join(IMAGE_DIR, fname)
    if not os.path.exists(path):
        pytest.skip(f"{fname} not found in {IMAGE_DIR}")

    cfg = Config(calibration=CalibrationConfig(um_per_px=UM_PER_PX_4X))
    area = analyze_image(path, cfg).metrics.area

    rel = abs(area - expected) / expected
    assert rel < 0.01, (
        f"{fname}: area {area:.1f} um^2 differs from pinned {expected:.1f} um^2 "
        f"by {100 * rel:.2f}%. Segmentation behaviour has changed."
    )


@needs_images
def test_batch1_treated_smaller_than_control():
    """Sanity: treated spheroids must measure smaller than controls.

    Not a biological claim (different timepoints) - a guard against a
    catastrophic segmentation failure inverting the groups.
    """
    ctrl = [v for k, v in BATCH1_EXPECTED_AREA_UM2.items() if not k.startswith("After")]
    treated = [v for k, v in BATCH1_EXPECTED_AREA_UM2.items() if k.startswith("After")]
    assert max(treated) < min(ctrl)


# --------------------------------------------------------------------------
# Layer 3: pinned measurements on the bundled example images
#
# Unlike layer 2, these images ship with the repository, so these tests run
# everywhere - including CI and on a reviewer's machine. They are the only
# tests that exercise the full pipeline on real microscopy data by default.
#
# The expected values are the ones reported for these two images in the
# associated Application Note. If they drift, either the segmentation changed
# or the bundled files did; both invalidate the published figures.
# --------------------------------------------------------------------------

EXAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "examples", "data")

EXAMPLE_EXPECTED = {
    # filename: (area um^2, equivalent diameter um, circularity)
    "control_24h_03.png": (104859.7, 365.4, 0.298),
    "treated_48h_01.png": (114563.4, 381.9, 0.312),
}

needs_examples = pytest.mark.skipif(
    not os.path.isdir(EXAMPLE_DIR),
    reason="bundled example images are missing from examples/data",
)


@needs_examples
@pytest.mark.parametrize("fname,expected", sorted(EXAMPLE_EXPECTED.items()))
def test_bundled_example_measurements_are_stable(fname, expected):
    """Bundled examples must reproduce the published per-image measurements."""
    from spheroidkit import analyze_image

    path = os.path.join(EXAMPLE_DIR, fname)
    assert os.path.isfile(path), f"bundled example missing: {path}"

    exp_area, exp_diam, exp_circ = expected
    cfg = Config(calibration=CalibrationConfig(um_per_px=UM_PER_PX_4X))
    m = analyze_image(path, cfg).metrics

    rel = abs(m.area - exp_area) / exp_area
    assert rel < 0.001, (
        f"{fname}: area {m.area:.1f} um^2 differs from the published "
        f"{exp_area:.1f} um^2 by {100 * rel:.3f}%."
    )
    assert abs(m.eq_diameter - exp_diam) < 0.1, (
        f"{fname}: equivalent diameter {m.eq_diameter:.1f} um differs from the "
        f"published {exp_diam:.1f} um."
    )
    assert abs(m.circularity - exp_circ) < 0.001, (
        f"{fname}: circularity {m.circularity:.3f} differs from the published "
        f"{exp_circ:.3f}."
    )


@needs_examples
def test_bundled_examples_are_rgb():
    """The bundled files must stay 3-channel.

    Pre-converting them to 8-bit grayscale with a different luminance weighting
    than cv2's shifts the measured area by up to 0.34% and breaks the published
    values pinned above.
    """
    import cv2

    for fname in EXAMPLE_EXPECTED:
        img = cv2.imread(os.path.join(EXAMPLE_DIR, fname), cv2.IMREAD_UNCHANGED)
        assert img is not None, f"could not read {fname}"
        assert img.ndim == 3 and img.shape[2] == 3, (
            f"{fname} must be 3-channel RGB, got shape {img.shape}"
        )
