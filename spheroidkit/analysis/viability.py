"""
Viability proxy (Stage 7): a transparent MORPHOLOGICAL surrogate for viability.

IMPORTANT SCIENTIFIC CAVEAT:
Phase-contrast / brightfield images cannot measure true live/dead viability
(that needs calcein/PI or similar fluorescent stains). This module computes a
composite morphological index that CORRELATES with deterioration: a healthy
spheroid is compact, smooth, circular and densely textured; a deteriorating one
becomes ragged, less circular, and texturally heterogeneous. The output is
explicitly a surrogate and is flagged as such. It must NOT be reported as
validated viability.
"""
from dataclasses import dataclass, asdict
import numpy as np
from skimage import measure


@dataclass
class ViabilityProxy:
    index: float                # 0-1 composite; higher = more "healthy" morphology
    circularity: float
    solidity: float             # area / convex area; compactness
    texture_homogeneity: float  # 0-1; higher = more uniform (denser core)
    is_surrogate: bool = True   # always True; for honest labelling downstream
    note: str = ("Morphological surrogate from brightfield/phase contrast; "
                 "NOT fluorescence-validated viability.")

    def as_dict(self) -> dict:
        return asdict(self)


def _solidity(mask: np.ndarray) -> float:
    props = max(measure.regionprops(mask.astype(int)), key=lambda r: r.area)
    return float(props.solidity)


def _texture_homogeneity(flat8: np.ndarray, mask: np.ndarray) -> float:
    """Inverse of normalised intra-spheroid intensity variance (0-1).

    A compact, dense spheroid has a relatively uniform interior; deterioration
    increases heterogeneity. We map low variance -> high homogeneity.
    """
    vals = flat8[mask]
    if vals.size == 0:
        return 0.0
    var = np.var(vals.astype(np.float32))
    # normalise against the theoretical max variance for 8-bit data
    return float(np.clip(1.0 - var / (128.0 ** 2), 0.0, 1.0))


def viability_proxy(flat8: np.ndarray, mask: np.ndarray,
                    circularity: float) -> ViabilityProxy:
    """Composite morphological health index from the segmented spheroid.

    Index = mean of circularity, solidity, and texture homogeneity. All three
    decline as a spheroid deteriorates, so their mean is a simple, explainable
    surrogate. Weights are equal and transparent by design.
    """
    sol = _solidity(mask)
    tex = _texture_homogeneity(flat8, mask)
    idx = float(np.mean([np.clip(circularity, 0, 1), sol, tex]))
    return ViabilityProxy(index=idx, circularity=float(circularity),
                          solidity=sol, texture_homogeneity=tex)
