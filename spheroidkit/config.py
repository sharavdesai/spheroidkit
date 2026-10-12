"""
Central configuration for spheroidkit.

Every tunable parameter lives here so behaviour can be adjusted in one place
without editing algorithm code. Values were validated on real A549 phase/bright-
field images (samples 0017, 0019).
"""
from dataclasses import dataclass, field


@dataclass
class PreprocessConfig:
    # Channel used for intensity (warm RGB -> green carries best contrast)
    channel: str = "green"            # "green" | "luminance" | "gray"
    # Sigma for the large-Gaussian background model (illumination flattening).
    # Large relative to spheroid so it models background, not the object.
    bg_sigma: float = 80.0


@dataclass
class SegmentConfig:
    # Local-entropy texture analysis window radius (px)
    entropy_radius: int = 9
    # Minimum object size to keep (px) - removes specks/debris
    min_object_size: int = 2000
    # Morphological opening radius (px) - applied BEFORE closing.
    # Severs the thin texture bridges that otherwise merge the corona of shed,
    # disaggregated cells around a drug-treated spheroid into the main object.
    # 0 = off (pre-v1.1 behaviour).
    opening_radius: int = 4
    # Morphological closing radius (px) - merges gaps in texture mask
    closing_radius: int = 7
    # Minimum area for the central-object candidate (px)
    min_central_area: int = 5000
    # Boundary smoothing: Gaussian sigma applied to the mask edge.
    # 0 = off (raw scalloped edge); higher = smoother perimeter.
    # This lifts circularity without moving the boundary's true position.
    boundary_smooth_sigma: float = 4.0
    # How much of the diffuse outer corona to include.
    # Otsu offset on the texture map: higher = tighter (denser core only),
    # lower = looser (include more loose peripheral cells).
    #
    # 0.12 was fixed on the batch-1 development set of 8 calibrated 4x A549
    # images (5 control, 3 treated) against expert manual ImageJ tracings.
    # Relative to the pre-v1.1 default of 0.0 it reduced mean area bias from
    # +4.5% to +0.6% (control) and +35.3% to +14.7% (treated), and raised
    # overall Lin's CCC from 0.876 to 0.985.
    #
    # NOTE: those figures are development-set values - the parameter was tuned
    # on the same images it was scored on - and are NOT validation results.
    # This value is deliberately FROZEN so that a held-out batch can be scored
    # honestly. Do not re-tune it on data you intend to report.
    edge_tightness: float = 0.12


@dataclass
class CalibrationConfig:
    # Microns per pixel. None => measurements reported in pixels (relative only).
    um_per_px: float | None = None

    @property
    def calibrated(self) -> bool:
        return self.um_per_px is not None


@dataclass
class Config:
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    segment: SegmentConfig = field(default_factory=SegmentConfig)
    calibration: CalibrationConfig = field(default_factory=CalibrationConfig)


# A ready-to-use default, validated on the sample images.
DEFAULT = Config()
