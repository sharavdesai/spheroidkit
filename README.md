# spheroidkit

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23311574.svg)](https://doi.org/10.5281/zenodo.23311574)
[![PyPI](https://img.shields.io/pypi/v/spheroidkit.svg)](https://pypi.org/project/spheroidkit/)
[![tests](https://github.com/sharavdesai/spheroidkit/actions/workflows/tests.yml/badge.svg)](https://github.com/sharavdesai/spheroidkit/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Open, no-install toolkit for end-to-end tumour spheroid analysis from brightfield / phase-contrast microscopy.**

spheroidkit takes microscopy images of multicellular tumour spheroids (MCTS) and carries them through the *entire* analysis workflow in one place — segmentation, shape-aware size measurement, growth tracking, dose-response (IC50) fitting, and group statistics — without installation, login, or programming. Unlike tools that stop at segmentation and leave you to fit curves elsewhere, spheroidkit closes the loop from raw image to publication-ready drug-response result.

It uses transparent **classical image processing** (no training data, no GPU, fully reproducible and explainable) and is robust to the uneven illumination and diffuse spheroid borders of real laboratory images. Input is format-agnostic (JPEG, PNG, TIFF) with flexible post-hoc micron calibration.

## Key features

- Texture-based segmentation robust to phase-contrast/brightfield halo, vignetting, and debris
- Shape-aware metrics: projected area, equivalent diameter, major/minor axes, circularity, ellipsoidal volume (flagged by circularity for honest reporting)
- Growth tracking across user-defined, unevenly spaced timepoints with fold-change normalisation, specific growth rate, and doubling time
- Dose-response: 4-parameter logistic (Hill) IC50 fitting with bootstrap confidence intervals and goodness-of-fit
- Group statistics: Mann-Whitney / Kruskal-Wallis with Holm-Bonferroni correction
- Optional morphological viability surrogate (explicitly labelled — not a substitute for fluorescence viability)
- Whole-plate batch processing with per-well error isolation
- Validation module: tool-vs-manual agreement (Pearson, Lin's CCC, Bland-Altman, Dice/IoU)
- Optional no-install web interface

## Installation

    pip install spheroidkit            # core library
    pip install spheroidkit[web]       # + web interface
    pip install spheroidkit[dev]       # + testing / plotting tools

Requires Python 3.10+.

## Quick start (library)

```python
from spheroidkit import analyze_image, Config, CalibrationConfig

# Pixel units (no calibration)
result = analyze_image("spheroid.tif")
print(result.metrics.as_dict())

# Real units: supply microns-per-pixel for your objective
cfg = Config(calibration=CalibrationConfig(um_per_px=1.55))
result = analyze_image("spheroid.tif", cfg)
```

Growth curve across timepoints:

```python
from spheroidkit import build_growth_curve, TimePoint

curve = build_growth_curve([
    TimePoint(24,  820000, label="24h"),
    TimePoint(72,  1010000, label="day 3"),
    TimePoint(120, 1280000, label="day 5"),
    TimePoint(168, 1520000, label="day 7"),
], metric="area")
print(curve.specific_growth_rate, curve.doubling_time_h)
```

Dose-response / IC50:

```python
from spheroidkit import fit_dose_response

fit = fit_dose_response(
    concentrations=[0.1, 0.3, 1.0, 3.0, 10.0, 30.0],
    responses=[96, 82, 55, 28, 12, 6],   # % of control
    units="uM")
print(fit.ic50, fit.ic50_ci, fit.r_squared)
```

## Web interface

    pip install spheroidkit[web]
    spheroidkit-serve                  # http://127.0.0.1:8000
    spheroidkit-serve --port 9000
    spheroidkit-serve --host 0.0.0.0   # expose on network / containers

## Running the tests

    pip install spheroidkit[dev]
    pytest

## Citation

If you use spheroidkit in your research, please cite:

> Desai, S. A. spheroidkit: an open, no-install toolkit for end-to-end tumour
> spheroid growth and drug-response analysis from brightfield microscopy. (2026).

*(An accompanying Application Note is in preparation; update this entry with the DOI/journal on publication.)*

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 Sharav A. Desai.

## Author

**Sharav A. Desai** — Department of Pharmaceutical Biotechnology, Sanjivani College of Pharmaceutical Education and Research (Autonomous), Kopargaon, Maharashtra, India.


## How to cite

If spheroidkit contributes to work you publish, please cite the software archive:

> Desai, S. A., Patel, V., Chaudhary, N., Mehta, A., Baswekar, A. G., & Nevase, G. S. (2026).
> *spheroidkit: a transparent, no-training open-source tool for end-to-end measurement of
> tumour spheroids* (Version 1.1.0) [Computer software]. Zenodo.
> https://doi.org/10.5281/zenodo.23311574

- **Concept DOI** [10.5281/zenodo.23311574](https://doi.org/10.5281/zenodo.23311574) — always resolves to the latest version; use this one unless you need to pin a version.
- **Version DOI (v1.1.0)** [10.5281/zenodo.23311575](https://doi.org/10.5281/zenodo.23311575) — the exact release validated in the Application Note.

`CITATION.cff` in this repository carries the same metadata in machine-readable form; GitHub's
"Cite this repository" button reads it directly.
