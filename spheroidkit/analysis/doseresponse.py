"""
Dose-response (Stage 6): fit a concentration-response curve and extract IC50.

Design notes (grounded in real dasatinib/axitinib workflow):
- Response = growth inhibition relative to untreated control (% of control),
  derived from the Stage-5 growth output. Curve runs ~100% (no drug) -> 0%.
- Model = 4-parameter logistic (4PL / Hill equation), the pharmacological
  standard, fit on a log10(concentration) axis.
- Reports IC50 with a bootstrap confidence interval, Hill slope, asymptotes,
  and R^2 goodness-of-fit, because manuscripts and reviewers require them.
"""
from dataclasses import dataclass, asdict
import warnings
import numpy as np
from scipy.optimize import curve_fit, OptimizeWarning


def hill_4pl(log_conc, bottom, top, log_ic50, hill):
    """4-parameter logistic on a log10(concentration) axis.

    bottom/top = lower/upper response asymptotes; log_ic50 = log10(IC50);
    hill = slope. Response decreases with concentration for inhibition.
    """
    return bottom + (top - bottom) / (1.0 + 10.0 ** ((log_conc - log_ic50) * hill))


@dataclass
class DoseResponseFit:
    ic50: float                 # in concentration units (same as input)
    ic50_ci: tuple              # (low, high) bootstrap 95% CI
    hill_slope: float
    top: float
    bottom: float
    r_squared: float
    log_ic50: float
    units: str                  # concentration units label, e.g. "uM"
    n_points: int

    def as_dict(self) -> dict:
        d = asdict(self)
        d["ic50_ci"] = list(self.ic50_ci)
        return d


def response_from_growth(treated_growth, control_growth):
    """Convert growth values to % of control (100 = no inhibition)."""
    treated = np.asarray(treated_growth, dtype=float)
    return 100.0 * treated / (float(control_growth) + 1e-12)


def _r_squared(y, y_pred):
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return float(1.0 - ss_res / (ss_tot + 1e-12))


def fit_dose_response(
    concentrations,
    responses,
    units: str = "uM",
    n_boot: int = 1000,
    seed: int = 0,
) -> DoseResponseFit:
    """Fit a 4PL curve. concentrations in real units (>0), responses in % control."""
    conc = np.asarray(concentrations, dtype=float)
    resp = np.asarray(responses, dtype=float)
    if np.any(conc <= 0):
        raise ValueError("concentrations must be > 0 for a log axis")

    logc = np.log10(conc)
    p0 = [resp.min(), resp.max(), np.median(logc), 1.0]
    bounds = ([-50, 50, logc.min() - 2, 0.1],
              [50, 150, logc.max() + 2, 10])

    # OptimizeWarning ("covariance could not be estimated") is benign here: we do
    # not use curve_fit's covariance (we bootstrap the CI ourselves), and some
    # residual resamples fit perfectly, leaving covariance undefined. Suppress it
    # locally so it does not alarm users, without hiding other warnings.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        popt, _ = curve_fit(hill_4pl, logc, resp, p0=p0, bounds=bounds, maxfev=20000)
        bottom, top, log_ic50, hill = popt
        y_pred = hill_4pl(logc, *popt)
        r2 = _r_squared(resp, y_pred)

        # Bootstrap CI for IC50 by resampling residuals
        rng = np.random.default_rng(seed)
        resid = resp - y_pred
        boot_ic50 = []
        for _ in range(n_boot):
            ys = y_pred + rng.choice(resid, size=resid.size, replace=True)
            try:
                bp, _ = curve_fit(hill_4pl, logc, ys, p0=popt, bounds=bounds, maxfev=20000)
                boot_ic50.append(10.0 ** bp[2])
            except Exception:
                continue
    if boot_ic50:
        lo, hi = np.percentile(boot_ic50, [2.5, 97.5])
    else:
        lo = hi = float("nan")

    return DoseResponseFit(
        ic50=float(10.0 ** log_ic50),
        ic50_ci=(float(lo), float(hi)),
        hill_slope=float(hill), top=float(top), bottom=float(bottom),
        r_squared=r2, log_ic50=float(log_ic50), units=units,
        n_points=int(conc.size),
    )


def curve_points(fit: DoseResponseFit, n: int = 100):
    """Smooth curve for plotting: returns (concentrations, responses)."""
    lo = fit.log_ic50 - 3
    hi = fit.log_ic50 + 3
    logc = np.linspace(lo, hi, n)
    resp = hill_4pl(logc, fit.bottom, fit.top, fit.log_ic50, fit.hill_slope)
    return 10.0 ** logc, resp
