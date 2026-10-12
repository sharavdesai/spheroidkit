# Contributing to spheroidkit

Thank you for your interest. This is a small scientific tool maintained
alongside active research, so please keep contributions focused and
well-described.

## Reporting a problem

Open an issue at
<https://github.com/sharavdesai/spheroidkit/issues> and include:

- the spheroidkit version (`python -c "import spheroidkit; print(spheroidkit.__version__)"`)
- your Python version and operating system
- the exact command or code you ran, and the full traceback if there was one
- what you expected versus what happened
- if segmentation is the problem, the input image (or a representative one) and
  the calibration factor you used

Before reporting a measurement problem, please run `python examples/run_samples.py`
and say whether it reproduces the values in `examples/data/README.md`. That
distinguishes an installation problem from a genuine defect.

## Running the tests

    git clone https://github.com/sharavdesai/spheroidkit.git
    cd spheroidkit
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -e ".[dev]"
    pytest -v

The suite must pass on Python 3.10 through 3.13. Continuous integration runs
the same matrix on every push.

## Submitting a change

1. Open an issue first for anything beyond a typo, so the approach can be agreed.
2. Branch from `main`, keep the change focused, and add or update a test.
3. Run `pytest -v` and `python examples/run_samples.py` before opening the pull request.
4. Add an entry to `CHANGELOG.md` under an "Unreleased" heading.

## A note on segmentation parameters

`SegmentConfig.edge_tightness` and `SegmentConfig.opening_radius` were fixed on
a development set and deliberately frozen so that held-out validation data can
be scored honestly. **Please do not submit pull requests that re-tune these
defaults** on data that has been, or will be, used to report accuracy. If you
find a case the defaults handle poorly, open an issue with the image rather
than changing the default — per-study overrides are supported through `Config`.

## Licence

Contributions are accepted under the MIT licence that covers this project.
The bundled example images in `examples/data/` are CC BY 4.0, not MIT.
