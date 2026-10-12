"""
Measurement: shape-aware metrics with optional micron calibration.

Reports projected area (assumption-free, primary), axes, ellipsoidal volume
(model-based, flagged by circularity), and circularity (both a readout and a
confidence flag for the volume estimate). Honest about 2D-projection limits.
"""
from dataclasses import dataclass, asdict
import numpy as np
from skimage import measure

from ..config import CalibrationConfig


@dataclass
class SpheroidMetrics:
    area: float
    eq_diameter: float
    major_axis: float
    minor_axis: float
    perimeter: float
    circularity: float          # 4*pi*A / P^2 ; 1.0 = perfect circle
    volume: float               # ellipsoidal estimate
    units: str                  # "px" or "um"
    volume_reliable: bool       # circularity-based flag

    def as_dict(self) -> dict:
        return asdict(self)


def measure_mask(mask: np.ndarray, cal: CalibrationConfig) -> SpheroidMetrics:
    """Compute metrics from a boolean mask, applying calibration if present."""
    props = max(measure.regionprops(mask.astype(int)), key=lambda r: r.area)

    area_px = float(props.area)
    major_px = float(props.axis_major_length)
    minor_px = float(props.axis_minor_length)
    perim_px = float(props.perimeter)
    eqd_px = float(props.equivalent_diameter_area)
    circ = 4 * np.pi * area_px / (perim_px ** 2 + 1e-6)
    # prolate-ellipsoid volume from projected axes
    vol_px3 = (np.pi / 6.0) * major_px * (minor_px ** 2)

    if cal.calibrated:
        s = cal.um_per_px
        return SpheroidMetrics(
            area=area_px * s * s,
            eq_diameter=eqd_px * s,
            major_axis=major_px * s,
            minor_axis=minor_px * s,
            perimeter=perim_px * s,
            circularity=circ,
            volume=vol_px3 * s ** 3,
            units="um",
            volume_reliable=circ >= 0.85,
        )
    return SpheroidMetrics(
        area=area_px, eq_diameter=eqd_px, major_axis=major_px,
        minor_axis=minor_px, perimeter=perim_px, circularity=circ,
        volume=vol_px3, units="px", volume_reliable=circ >= 0.85,
    )
