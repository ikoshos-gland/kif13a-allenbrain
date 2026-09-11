"""Separate detection rate from expression level in the whole-brain ranking.

Why this matters. The ranking column `mean_Kif13a` is the mean of log2(CPM + 1)
taken over every cell in a subclass, including the cells where nothing was
detected. A non-detected cell contributes exactly 0 to that mean, so

    mean_over_all_cells = fraction_expressing * mean_over_expressing_cells

is an exact identity, not an approximation. That makes the mean a blend of two
different things: how often the gene is detected, and how high it reads when it
is. Raising 2 to the difference of two such means therefore does NOT give a fold
change in expression, because the mean of a log is not the log of a mean.

This script splits the two apart. It shows that the large apparent gap between
oligodendrocytes and other glia is driven mostly by detection rate, and that
among cells where Kif13a is detected the differences are modest.

Detection rate in 10x data tracks how much RNA a cell type contains, which is a
known technical confounder. Pericytes are the clearest warning: they rank last
overall, yet among detecting pericytes the level is higher than in astrocytes.

Input : results/derived_wholebrain_subclass_ranking.csv
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

REFERENCE = "327 Oligo NN"
FOCUS = [
    "327 Oligo NN", "326 OPC NN", "334 Microglia NN", "335 BAM NN",
    "318 Astro-NT NN", "319 Astro-TE NN", "316 Bergmann NN",
    "333 Endo NN", "332 SMC NN", "331 Peri NN", "330 VLMC NN",
]

r = pd.read_csv(RESULTS / "derived_wholebrain_subclass_ranking.csv")
d = r[r.subclass.isin(FOCUS)].copy()
d["rank_overall"] = d.subclass.map({s: i for i, s in enumerate(r.subclass, start=1)})

# Exact decomposition: non-detected cells contribute 0 to the mean of log2(CPM+1)
d["mean_among_expressing"] = d.mean_Kif13a / d.fraction_expressing
d["cpm_among_expressing"] = 2 ** d.mean_among_expressing - 1

ref = d[d.subclass == REFERENCE].iloc[0]

# The figure that looks right but is not: 2 ** (difference of means including zeros)
d["naive_fold"] = 2 ** (ref.mean_Kif13a - d.mean_Kif13a)
# What actually drives it
d["detection_ratio"] = ref.fraction_expressing / d.fraction_expressing
d["level_ratio_among_expressing"] = ref.cpm_among_expressing / d.cpm_among_expressing

d = d.sort_values("mean_Kif13a", ascending=False)

cols = ["subclass", "rank_overall", "n_cells", "mean_Kif13a", "fraction_expressing",
        "mean_among_expressing", "cpm_among_expressing",
        "naive_fold", "detection_ratio", "level_ratio_among_expressing"]

print("Reference for all ratios:", REFERENCE)
print()
print(d[cols].round(3).to_string(index=False))

print("\nRead this as follows.")
print("  naive_fold                   = 2 ** (difference of means that include zeros). MISLEADING.")
print("  detection_ratio              = how many times more often the gene is detected.")
print("  level_ratio_among_expressing = how many times higher it reads where it IS detected.")

astro = d[d.subclass == "319 Astro-TE NN"].iloc[0]
print(f"\nWorked example, oligodendrocyte vs telencephalic astrocyte:")
print(f"  naive figure                     {astro.naive_fold:.1f}x")
print(f"  detection rate                   {ref.fraction_expressing:.3f} vs {astro.fraction_expressing:.3f}"
      f"  ({astro.detection_ratio:.2f}x)")
print(f"  level where detected             {ref.cpm_among_expressing:.0f} vs {astro.cpm_among_expressing:.0f} CPM"
      f"  ({astro.level_ratio_among_expressing:.2f}x)")

peri = d[d.subclass == "331 Peri NN"].iloc[0]
print(f"\nWarning case, pericyte: ranks {int(peri.rank_overall)} of 265 overall, naive figure"
      f" {peri.naive_fold:.1f}x lower,")
print(f"  yet among detecting pericytes the level is {peri.cpm_among_expressing:.0f} CPM,"
      f" above the astrocyte {astro.cpm_among_expressing:.0f} CPM.")
print("  Pericytes carry little RNA, so their low rank is plausibly technical.")

out = RESULTS / "derived_detection_vs_level.csv"
d[cols].to_csv(out, index=False)
print(f"\nSaved: {out}")
