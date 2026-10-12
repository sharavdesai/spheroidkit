"""
Segmentation: texture-based detection of a single central spheroid.

Approach (validated on real A549 images): the spheroid is a high-texture
(granular) island in a low-texture (smooth) background. Local entropy turns this
into a thresholdable map; we keep the largest central object and reject debris.
Optional boundary smoothing cleans the perimeter without moving the edge.
"""
import numpy as np
from skimage import filters, morphology, measure
from skimage.filters.rank import entropy
from skimage.morphology import disk
from scipy import ndimage as ndi

from ..config import SegmentConfig


def texture_map(flat8: np.ndarray, radius: int = 9) -> np.ndarray:
    """Local-entropy texture map, normalised to [0, 1]."""
    e = entropy(flat8, disk(radius))
    return (e - e.min()) / (np.ptp(e) + 1e-6)


def _largest_central(mask: np.ndarray, min_area: int) -> np.ndarray:
    """Keep the object nearest the image centre (rejects debris/artifacts)."""
    lbl = measure.label(mask)
    if lbl.max() == 0:
        return mask
    cy, cx = mask.shape[0] / 2, mask.shape[1] / 2
    best, best_d = None, np.inf
    for r in measure.regionprops(lbl):
        y, x = r.centroid
        d = (y - cy) ** 2 + (x - cx) ** 2
        if r.area > min_area and d < best_d:
            best_d, best = d, r.label
    return (lbl == best) if best is not None else mask


def _smooth_boundary(mask: np.ndarray, sigma: float) -> np.ndarray:
    """Smooth the perimeter via Gaussian on the mask, re-threshold at 0.5.

    Lifts circularity (removes scalloping) without shifting the true edge.
    """
    if sigma <= 0:
        return mask
    sm = ndi.gaussian_filter(mask.astype(float), sigma)
    return sm > 0.5


def _remove_small(mask: np.ndarray, min_size: int) -> np.ndarray:
    """Remove connected components smaller than min_size (px).

    Implemented directly rather than via skimage.remove_small_objects so the
    package is robust to that function's shifting parameter API across
    scikit-image versions.
    """
    lbl = measure.label(mask)
    if lbl.max() == 0:
        return mask
    counts = np.bincount(lbl.ravel())
    keep = np.where(counts >= min_size)[0]
    keep = keep[keep != 0]  # drop background label
    return np.isin(lbl, keep)


def segment(flat8: np.ndarray, cfg: SegmentConfig) -> np.ndarray:
    """Return a boolean mask of the single spheroid."""
    tex = texture_map(flat8, cfg.entropy_radius)
    thresh = filters.threshold_otsu(tex) + cfg.edge_tightness
    mask = tex > thresh
    mask = _remove_small(mask, cfg.min_object_size)
    if cfg.opening_radius > 0:
        # Opening BEFORE closing: breaks the thin bridges linking shed cells to
        # the spheroid body, so _largest_central selects the dense core rather
        # than core-plus-corona. Order matters - closing first would cement the
        # bridges in place.
        mask = morphology.opening(mask, disk(cfg.opening_radius))
    mask = morphology.closing(mask, disk(cfg.closing_radius))
    mask = ndi.binary_fill_holes(mask)
    mask = _largest_central(mask, cfg.min_central_area)
    mask = ndi.binary_fill_holes(mask)
    mask = _smooth_boundary(mask, cfg.boundary_smooth_sigma)
    return mask
