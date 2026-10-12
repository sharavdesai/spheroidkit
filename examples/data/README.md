# Example images

Two brightfield micrographs of A549 multicellular tumour spheroids (MCTS),
provided so that `examples/run_samples.py` runs out of the box and so that any
user can reproduce published measurements on known input.

| File | Condition | Timepoint |
|---|---|---|
| `control_24h_03.png` | A549, untreated control | 24 h |
| `treated_48h_01.png` | A549, drug-treated | 48 h |

## Acquisition

- Microscope: Olympus CKX53 inverted, brightfield
- Camera: Magcam DC5
- Objective: 4x
- Native resolution: 2592 x 1944 px, 24-bit RGB
- **Calibration: 0.21949 um/px**, determined with a stage micrometer
  (200 um = 911.178 px). Cross-check against the 10x factor (0.08803 um/px)
  gives a magnification ratio of 2.493 versus an expected 2.500 — 0.3 % agreement.

Both files are **lossless** conversions of the original 24-bit BMP acquisitions
(BMP to PNG, no resizing, cropping, channel conversion or lossy compression).
Pixel values are bit-identical to the originals, so measurements made on these
files are identical to measurements made on the raw acquisitions.

> Note on colour: these are stored as RGB, not grayscale, deliberately. The
> pipeline applies its own luminance weighting; pre-converting to 8-bit
> grayscale with a different weighting shifts the measured projected area by up
> to 0.34 %, which would stop these files reproducing the published values below.

## Expected output

Running `python examples/run_samples.py` from the repository root should print
the following, which are the same values reported for these two images in the
associated Application Note:

| Image | Projected area (um^2) | Equiv. diameter (um) | Major (um) | Minor (um) | Circularity |
|---|---|---|---|---|---|
| `control_24h_03` | 104,859.7 | 365.4 | 387.0 | 349.0 | 0.298 |
| `treated_48h_01` | 114,563.4 | 381.9 | 409.9 | 363.5 | 0.312 |

If your run reproduces these numbers, your installation is working correctly.
Any deviation indicates a changed configuration, a modified input file, or a
genuine regression — please open an issue.

## Scope

These two images are an **installation check and worked example only**. They are
not the validation dataset. The full 22-image held-out validation set, the expert
manual ImageJ region-of-interest files, the per-image manual and automated
measurements, and the analysis scripts reproducing all agreement statistics are
deposited separately; see the Data Availability statement of the Application Note.

## Licence

These two images are released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), separately from the
MIT licence that covers the source code. Please cite the Application Note if you
use them.
