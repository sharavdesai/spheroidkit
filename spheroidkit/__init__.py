"""
spheroidkit
===========

Open, no-install toolkit for end-to-end tumour spheroid analysis from
brightfield / phase-contrast microscopy: segmentation, shape-aware
measurement, growth tracking, dose-response (IC50) fitting, group statistics,
a morphological viability surrogate, and tool-vs-manual validation.

Quick start
-----------
    from spheroidkit import analyze_image
    result = analyze_image("spheroid.tif")
    print(result.metrics.as_dict())

    # Real-unit measurements: supply microns-per-pixel for your objective
    from spheroidkit import Config, CalibrationConfig
    cfg = Config(calibration=CalibrationConfig(um_per_px=1.55))
    result = analyze_image("spheroid.tif", cfg)
"""
# ---- Core pipeline (most common entry point) ----
from .pipeline import analyze_image, AnalysisResult
from .config import Config, DEFAULT, PreprocessConfig, SegmentConfig, CalibrationConfig

# ---- Analysis workflows (surfaced for convenience, scikit-learn style) ----
from .analysis.growth import build_growth_curve, GrowthCurve, TimePoint
from .analysis.doseresponse import fit_dose_response, DoseResponseFit, response_from_growth
from .analysis.stats import compare_two, compare_many, holm_bonferroni
from .analysis.viability import viability_proxy, ViabilityProxy
from .analysis.validation import agreement, dice_iou, AgreementResult

# ---- Batch / plate processing ----
from .io.batch import process_plate, build_dose_series, PlateResult

__version__ = "1.1.0"

__all__ = [
    "analyze_image", "AnalysisResult",
    "Config", "DEFAULT", "PreprocessConfig", "SegmentConfig", "CalibrationConfig",
    "build_growth_curve", "GrowthCurve", "TimePoint",
    "fit_dose_response", "DoseResponseFit", "response_from_growth",
    "compare_two", "compare_many", "holm_bonferroni",
    "viability_proxy", "ViabilityProxy",
    "agreement", "dice_iou", "AgreementResult",
    "process_plate", "build_dose_series", "PlateResult",
]
