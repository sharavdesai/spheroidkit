"""
Validation: quantify agreement between spheroidkit and a reference (manual)
segmentation. Produces the statistics an Application Note reviewer expects.

- Pearson r and concordance correlation coefficient (CCC, Lin's) on a chosen
  metric (e.g. area) across N spheroids.
- Bland-Altman: mean bias and 95% limits of agreement.
- Dice / IoU overlap when paired masks are available (spatial agreement).

The reference values are supplied by the user (e.g. manual ImageJ areas); this
module does not invent ground truth.
"""
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class AgreementResult:
    n: int
    pearson_r: float
    ccc: float                 # Lin's concordance correlation coefficient
    bias: float                # mean(tool - reference)
    loa_lower: float           # 95% limits of agreement
    loa_upper: float
    mean_abs_pct_error: float

    def as_dict(self) -> dict:
        return asdict(self)


def concordance_ccc(x, y) -> float:
    """Lin's concordance correlation coefficient."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    mx, my = x.mean(), y.mean()
    vx, vy = x.var(), y.var()
    cov = np.mean((x - mx) * (y - my))
    return float(2 * cov / (vx + vy + (mx - my) ** 2 + 1e-12))


def agreement(tool_values, reference_values) -> AgreementResult:
    """Tool-vs-reference agreement statistics for a single metric."""
    t = np.asarray(tool_values, float)
    r = np.asarray(reference_values, float)
    if t.size != r.size or t.size < 2:
        raise ValueError("need >=2 paired values of equal length")

    pearson = float(np.corrcoef(t, r)[0, 1])
    ccc = concordance_ccc(t, r)
    diff = t - r
    bias = float(diff.mean())
    sd = float(diff.std(ddof=1))
    mape = float(np.mean(np.abs(diff) / (np.abs(r) + 1e-12)) * 100)
    return AgreementResult(
        n=int(t.size), pearson_r=pearson, ccc=ccc, bias=bias,
        loa_lower=bias - 1.96 * sd, loa_upper=bias + 1.96 * sd,
        mean_abs_pct_error=mape,
    )


def dice_iou(mask_a: np.ndarray, mask_b: np.ndarray):
    """Spatial overlap between two boolean masks: (Dice, IoU)."""
    a = mask_a.astype(bool); b = mask_b.astype(bool)
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    dice = float(2 * inter / (a.sum() + b.sum() + 1e-12))
    iou = float(inter / (union + 1e-12))
    return dice, iou
