"""
spheroidkit — worked example
============================

Analyses the two bundled A549 spheroid images, prints the measured metrics in
real units, and writes segmentation overlays to ``examples/output/``.

Run from the repository root (or anywhere):

    python examples/run_samples.py

The bundled images are brightfield micrographs acquired at 4x on an Olympus
CKX53 with a Magcam DC5 camera, 2592 x 1944 px. The calibration factor below
(0.21949 um/px) was determined with a stage micrometer and is the same factor
used in the Application Note; see ``examples/data/README.md``.
"""
from __future__ import annotations

import os
import sys

# Allow running from a source checkout without installing the package first.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if os.path.isdir(os.path.join(_ROOT, "spheroidkit")):
    sys.path.insert(0, _ROOT)

import matplotlib

matplotlib.use("Agg")  # headless: no display required
import matplotlib.pyplot as plt

from spheroidkit import analyze_image, Config, CalibrationConfig

# Microscope calibration for the bundled images (4x objective, 2592x1944 px).
# Replace with the factor for your own objective and camera.
UM_PER_PX_4X = 0.21949

DATA_DIR = os.path.join(_HERE, "data")
OUT_DIR = os.path.join(_HERE, "output")

SAMPLES = [
    ("control_24h_03.png", "A549 control, 24 h"),
    ("treated_48h_01.png", "A549 treated, 48 h"),
]


def main() -> int:
    if not os.path.isdir(DATA_DIR):
        print(f"ERROR: example data directory not found: {DATA_DIR}", file=sys.stderr)
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    cfg = Config(calibration=CalibrationConfig(um_per_px=UM_PER_PX_4X))

    print(f"spheroidkit example run  |  calibration = {UM_PER_PX_4X} um/px (4x)\n")

    missing = 0
    for filename, label in SAMPLES:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.isfile(path):
            print(f"SKIP  {filename}: file not found", file=sys.stderr)
            missing += 1
            continue

        result = analyze_image(path, cfg)
        m = result.metrics
        stem = os.path.splitext(filename)[0]

        print(f"{stem}  ({label})")
        print(f"    projected area   = {m.area:,.1f} {m.units}^2")
        print(f"    equiv. diameter  = {m.eq_diameter:,.1f} {m.units}")
        print(f"    major / minor    = {m.major_axis:,.1f} / {m.minor_axis:,.1f} {m.units}")
        print(f"    circularity      = {m.circularity:.3f}")

        fig, ax = plt.subplots(figsize=(9, 7))
        ax.imshow(result.rgb)
        for contour in result.contour():
            ax.plot(contour[:, 1], contour[:, 0], "-", lw=2.5, color="cyan")
        ax.axis("off")
        ax.set_title(
            f"{stem} — area {m.area:,.0f} {m.units}$^2$, "
            f"circularity {m.circularity:.2f}"
        )
        out_path = os.path.join(OUT_DIR, f"{stem}_overlay.png")
        fig.savefig(out_path, dpi=110, bbox_inches="tight")
        plt.close(fig)
        print(f"    overlay written  -> {os.path.relpath(out_path, _ROOT)}\n")

    if missing:
        print(f"{missing} image(s) missing — see examples/data/README.md", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
