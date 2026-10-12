"""
Growth tracking (Stage 5): turn measurements of one spheroid across timepoints
into a growth curve with fold-change normalisation and growth-rate metrics.

Design notes (grounded in real workflow):
- Timepoints are user-defined and UNEVENLY spaced (e.g. 24h, then day 3/5/7).
  Times are given in hours; everything is plotted against real elapsed time.
- Baseline t0 defaults to the earliest timepoint (the 24h compaction point),
  the biologically meaningful start of measurable growth.
- Growth is reported absolute AND normalised (fold-change vs baseline), because
  dose-response (Stage 6) consumes fold-change / growth-inhibition.
"""
from dataclasses import dataclass, field
from typing import Literal
import numpy as np


@dataclass
class TimePoint:
    time_h: float                 # elapsed hours from seeding
    metric_value: float           # area or volume (calibrated or px)
    units: str = "px"             # "px" or "um"
    label: str | None = None      # e.g. "24h", "day 3"


@dataclass
class GrowthCurve:
    """Growth of a single spheroid over time."""
    times_h: np.ndarray
    values: np.ndarray            # absolute metric (area or volume)
    fold_change: np.ndarray       # normalised to baseline
    baseline_value: float
    metric: str                   # "area" or "volume"
    units: str
    labels: list[str] = field(default_factory=list)

    @property
    def specific_growth_rate(self) -> float:
        """Mean specific growth rate mu (1/h) from baseline to last point.

        mu = ln(V_end / V_0) / (t_end - t_0)
        """
        dt = self.times_h[-1] - self.times_h[0]
        if dt <= 0 or self.baseline_value <= 0:
            return float("nan")
        return float(np.log(self.values[-1] / self.baseline_value) / dt)

    @property
    def doubling_time_h(self) -> float:
        """Doubling time (h) implied by the specific growth rate."""
        mu = self.specific_growth_rate
        if not np.isfinite(mu) or mu <= 0:
            return float("nan")
        return float(np.log(2) / mu)

    def interval_rates(self) -> list[float]:
        """Specific growth rate within each consecutive interval (1/h)."""
        rates = []
        for i in range(1, len(self.times_h)):
            dt = self.times_h[i] - self.times_h[i - 1]
            v0, v1 = self.values[i - 1], self.values[i]
            rates.append(float(np.log(v1 / v0) / dt)
                         if dt > 0 and v0 > 0 else float("nan"))
        return rates

    def as_dict(self) -> dict:
        return {
            "metric": self.metric, "units": self.units,
            "times_h": self.times_h.tolist(),
            "values": self.values.tolist(),
            "fold_change": self.fold_change.tolist(),
            "baseline_value": self.baseline_value,
            "specific_growth_rate_per_h": self.specific_growth_rate,
            "doubling_time_h": self.doubling_time_h,
            "labels": self.labels,
        }


def build_growth_curve(
    points: list[TimePoint],
    metric: str = "area",
    baseline: Literal["first", "min"] | float = "first",
) -> GrowthCurve:
    """Assemble a GrowthCurve from timepoints.

    baseline: "first" (earliest time, default = 24h point), "min" (smallest
    value), or an explicit time_h value to use as the reference.
    """
    pts = sorted(points, key=lambda p: p.time_h)
    times = np.array([p.time_h for p in pts], dtype=float)
    values = np.array([p.metric_value for p in pts], dtype=float)
    labels = [p.label or f"{p.time_h:g}h" for p in pts]
    units = pts[0].units

    if baseline == "first":
        base = values[0]
    elif baseline == "min":
        base = values.min()
    else:  # explicit time
        idx = int(np.argmin(np.abs(times - float(baseline))))
        base = values[idx]

    fold = values / (base + 1e-9)
    return GrowthCurve(times_h=times, values=values, fold_change=fold,
                       baseline_value=float(base), metric=metric,
                       units=units, labels=labels)
