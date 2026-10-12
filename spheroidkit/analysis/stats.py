"""
Statistics: replicate group comparisons for treatment effects.

Provides the significance tests a drug study needs:
- two groups: Welch's t-test (parametric) or Mann-Whitney U (non-parametric)
- many groups: one-way ANOVA or Kruskal-Wallis
- multiple-comparison correction (Holm-Bonferroni) for per-concentration tests
The caller chooses parametric vs non-parametric; we default to non-parametric
for small replicate counts where normality cannot be assumed.
"""
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats


@dataclass
class TwoGroupResult:
    test: str
    statistic: float
    p_value: float
    n1: int
    n2: int
    significant: bool

    def as_dict(self) -> dict:
        return asdict(self)


def compare_two(control, treated, parametric: bool = False,
                alpha: float = 0.05) -> TwoGroupResult:
    a = np.asarray(control, float)
    b = np.asarray(treated, float)
    if parametric:
        stat, p = stats.ttest_ind(a, b, equal_var=False)  # Welch
        name = "Welch t-test"
    else:
        stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        name = "Mann-Whitney U"
    return TwoGroupResult(name, float(stat), float(p), a.size, b.size,
                          bool(p < alpha))


@dataclass
class MultiGroupResult:
    test: str
    statistic: float
    p_value: float
    n_groups: int
    significant: bool

    def as_dict(self) -> dict:
        return asdict(self)


def compare_many(groups: list, parametric: bool = False,
                 alpha: float = 0.05) -> MultiGroupResult:
    arrs = [np.asarray(g, float) for g in groups]
    if parametric:
        stat, p = stats.f_oneway(*arrs)
        name = "One-way ANOVA"
    else:
        stat, p = stats.kruskal(*arrs)
        name = "Kruskal-Wallis"
    return MultiGroupResult(name, float(stat), float(p), len(arrs),
                            bool(p < alpha))


def holm_bonferroni(p_values: list, alpha: float = 0.05):
    """Holm-Bonferroni step-down correction. Returns (adjusted_p, reject)."""
    p = np.asarray(p_values, float)
    order = np.argsort(p)
    m = p.size
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * p[idx]
        running = max(running, val)
        adj[idx] = min(running, 1.0)
    reject = adj < alpha
    return adj.tolist(), reject.tolist()
