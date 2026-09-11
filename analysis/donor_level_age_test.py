"""Donor-level adult vs aged test for Kif13a in OPC and mature oligodendrocytes.

The SLURM pipeline (scripts/run_kif13a_aging.py) reports group means only.
Testing at the cell level would treat thousands of cells from one mouse as
independent observations. This script collapses every mouse to a single value
first, then compares the 53 adult against the 44 aged donors.

Input : results/Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv
"""
from pathlib import Path
import pandas as pd
from scipy import stats

RESULTS = Path(__file__).resolve().parents[1] / "results"
d = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv")

out = []
for sc in sorted(d.subclass_name.unique()):
    s = d[d.subclass_name == sc]
    adult = s[s.donor_age_category == "adult"]["mean_Kif13a"].dropna()
    aged = s[s.donor_age_category == "aged"]["mean_Kif13a"].dropna()

    _, p_mw = stats.mannwhitneyu(aged, adult, alternative="two-sided")
    _, p_t = stats.ttest_ind(aged, adult, equal_var=False)

    # Cliff's delta: non-parametric effect size, robust to the log2 scale
    gt = sum(x > y for x in aged for y in adult)
    lt = sum(x < y for x in aged for y in adult)
    cliffs = (gt - lt) / (len(aged) * len(adult))

    delta = aged.mean() - adult.mean()
    out.append({
        "subclass": sc,
        "n_adult": len(adult), "n_aged": len(aged),
        "mean_adult": adult.mean(), "mean_aged": aged.mean(),
        "delta_log2": delta, "fold_change": 2 ** delta,
        "mannwhitney_p": p_mw, "welch_t_p": p_t, "cliffs_delta": cliffs,
    })

res = pd.DataFrame(out)
print(res.to_string(index=False))
res.to_csv(RESULTS / "derived_donor_level_age_test.csv", index=False)
