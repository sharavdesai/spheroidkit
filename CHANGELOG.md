# Changelog

All notable changes to spheroidkit are documented here.
This project follows [Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-10-10

The version validated in the associated Application Note. Changes are confined
to segmentation behaviour on drug-treated morphology and to warning handling in
dose-response fitting; the public API is unchanged.

### Changed

- **`SegmentConfig.edge_tightness` default: `0.0` → `0.12`.**
  Controls the Otsu offset on the texture map; higher values are tighter
  (denser core only), lower values include more of the loose peripheral corona.
  The value was fixed on a batch-1 **development** set of 8 calibrated 4x A549
  images (5 control, 3 treated) scored against expert manual ImageJ tracings.
  On that development set it reduced mean projected-area bias from +4.5 % to
  +0.6 % (control) and from +35.3 % to +14.7 % (treated), and raised Lin's
  concordance correlation coefficient from 0.876 to 0.985.

  > These are development-set figures: the parameter was tuned on the same
  > images it was scored on, so they are **not** validation results and must not
  > be reported as such. The value is deliberately frozen so that held-out data
  > can be scored honestly. Do not re-tune it on data you intend to report.

- Corrected the in-code description of `edge_tightness`, which previously
  described the sign of the offset the wrong way round.

- **Dose-response fitting** (`analysis/doseresponse.py`): scipy's
  `OptimizeWarning` ("covariance could not be estimated") is now suppressed
  locally inside the 4PL fit and its bootstrap. The warning is benign here —
  the covariance is never used, because the IC50 confidence interval is obtained
  by residual bootstrap — and some residual resamples fit perfectly, leaving the
  covariance undefined. The suppression is scoped to that block, so unrelated
  warnings still surface.

### Added

- **`SegmentConfig.opening_radius`, default 4 px.** A morphological opening is
  now applied *before* the existing closing step. It severs the thin texture
  bridges that otherwise connect the corona of shed, disaggregated cells around
  a drug-treated spheroid to the main object, so central-object selection
  returns the dense spheroid body rather than body-plus-corona. Order matters:
  closing first would cement those bridges in place. Set `opening_radius = 0`
  to restore pre-1.1 behaviour.

- Two bundled example images with documented provenance and calibration
  (`examples/data/`), so `examples/run_samples.py` runs without external files
  and reproduces published per-image measurements exactly.

- Continuous integration running the test suite on Python 3.10–3.13.

### Fixed

- `examples/run_samples.py` previously referenced hard-coded absolute paths that
  existed only on the development machine, so the example could not run
  anywhere else. It now resolves its inputs relative to the script location.

## [1.0.0] — 2026-06-18

Initial release: illumination correction, local-entropy texture segmentation,
shape-aware measurement, growth tracking, 4PL dose-response fitting with
bootstrap IC50 confidence intervals, non-parametric group statistics with
Holm–Bonferroni correction, a morphological viability surrogate, whole-plate
batch processing, tool-versus-manual agreement metrics, and an optional
FastAPI web interface.

[1.1.0]: https://github.com/sharavdesai/spheroidkit/releases/tag/v1.1.0
[1.0.0]: https://github.com/sharavdesai/spheroidkit/releases/tag/v1.0.0
