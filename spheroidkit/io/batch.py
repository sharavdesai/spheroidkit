"""
Batch / plate processing (Stage: scale-up): run the validated single-image
engine across a whole plate, assemble results by well, and feed concentration
series into dose-response automatically.

Design notes (grounded in real 96-well dose-response layout):
- Images map to wells by filename pattern (e.g. "...A01...") or an explicit map.
- A plate layout assigns each well a concentration + replicate group, so the
  tool knows controls vs treated and can build dose-response series.
- Each well is processed in isolation: one unreadable image is recorded as a
  per-well error and does not crash the whole plate run.
"""
from dataclasses import dataclass, field
import re
import glob
import os
import numpy as np

from ..config import Config, DEFAULT
from ..pipeline import analyze_image

WELL_RE = re.compile(r"([A-H])\s*0*([1-9][0-9]?)", re.IGNORECASE)


@dataclass
class WellResult:
    well: str
    path: str
    metrics: dict | None = None
    error: str | None = None
    concentration: float | None = None
    group: str | None = None


@dataclass
class PlateResult:
    wells: list[WellResult] = field(default_factory=list)

    @property
    def ok(self):
        return [w for w in self.wells if w.error is None]

    @property
    def failed(self):
        return [w for w in self.wells if w.error is not None]

    def summary(self) -> dict:
        return {"total": len(self.wells), "ok": len(self.ok),
                "failed": len(self.failed),
                "failed_wells": [w.well for w in self.failed]}


def parse_well_from_filename(path: str) -> str | None:
    """Extract a well id like 'A01' from a filename, or None."""
    name = os.path.basename(path)
    m = WELL_RE.search(name)
    if not m:
        return None
    return f"{m.group(1).upper()}{int(m.group(2)):02d}"


def process_plate(
    image_paths: list[str],
    layout: dict | None = None,
    cfg: Config = DEFAULT,
) -> PlateResult:
    """Run the engine over every image; attach concentration/group from layout.

    layout: optional {well_id: {"concentration": float, "group": str}}.
    """
    plate = PlateResult()
    for path in sorted(image_paths):
        well = parse_well_from_filename(path) or os.path.basename(path)
        wr = WellResult(well=well, path=path)
        if layout and well in layout:
            wr.concentration = layout[well].get("concentration")
            wr.group = layout[well].get("group")
        try:
            res = analyze_image(path, cfg)
            wr.metrics = res.metrics.as_dict()
        except Exception as e:  # isolate per-well failure
            wr.error = f"{type(e).__name__}: {e}"
        plate.wells.append(wr)
    return plate


def build_dose_series(
    plate: PlateResult,
    metric: str = "area",
    control_group: str = "control",
):
    """Collapse replicate wells into (concentrations, mean_response_%control).

    Returns dict with concentrations, responses, and per-point replicate counts,
    ready to hand to fit_dose_response().
    """
    # group successful wells by concentration
    by_conc: dict[float, list[float]] = {}
    control_vals: list[float] = []
    for w in plate.ok:
        val = w.metrics.get(metric)
        if val is None:
            continue
        if w.group == control_group or w.concentration in (0, 0.0, None):
            control_vals.append(val)
        elif w.concentration is not None:
            by_conc.setdefault(float(w.concentration), []).append(val)

    if not control_vals:
        raise ValueError("no control wells found to normalise against")
    control_mean = float(np.mean(control_vals))

    concs = sorted(by_conc.keys())
    responses, counts = [], []
    for c in concs:
        vals = by_conc[c]
        responses.append(100.0 * float(np.mean(vals)) / (control_mean + 1e-12))
        counts.append(len(vals))
    return {"concentrations": concs, "responses": responses,
            "replicates": counts, "control_mean": control_mean,
            "metric": metric}
