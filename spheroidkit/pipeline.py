"""
Pipeline: the single entry point that runs the validated core end-to-end.

    from spheroidkit import analyze_image
    result = analyze_image("0017.tif")
    print(result.metrics.as_dict())
"""
from dataclasses import dataclass
import numpy as np
import cv2
from skimage import measure

from .config import Config, DEFAULT
from .core.preprocess import preprocess
from .core.segment import segment
from .core.measure import measure_mask, SpheroidMetrics


@dataclass
class AnalysisResult:
    metrics: SpheroidMetrics
    mask: np.ndarray
    flat: np.ndarray
    rgb: np.ndarray
    viability: object = None

    def contour(self):
        """Return boundary coordinates for overlay plotting."""
        return measure.find_contours(self.mask.astype(float), 0.5)


def _load_rgb(path: str) -> np.ndarray:
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def analyze_image(path: str, cfg: Config = DEFAULT,
                  with_viability: bool = False) -> AnalysisResult:
    """Full pipeline: load -> preprocess -> segment -> measure.

    with_viability: also compute the optional morphological viability surrogate.
    """
    rgb = _load_rgb(path)
    flat = preprocess(rgb, cfg.preprocess)
    mask = segment(flat, cfg.segment)
    metrics = measure_mask(mask, cfg.calibration)
    result = AnalysisResult(metrics=metrics, mask=mask, flat=flat, rgb=rgb)
    if with_viability:
        from .analysis.viability import viability_proxy
        result.viability = viability_proxy(flat, mask, metrics.circularity)
    return result
