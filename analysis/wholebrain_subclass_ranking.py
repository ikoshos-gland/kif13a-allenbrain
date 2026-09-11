"""Rank all cell subclasses in the whole mouse brain by Kif13a expression.

The SLURM pipeline writes one subclass summary per anatomical partition.
This pools the 13 partitions into a single whole-brain ranking, weighting each
partition mean by its cell count. Subclasses below MIN_CELLS are dropped so that
the extremes are not driven by groups of a handful of cells.

Medians cannot be pooled from per-partition medians, so the ranking uses means.
Cells are pooled, not corrected per donor, so this ranking is descriptive.

Inputs : results/Kif13a_WMB-10Xv3-*_subclass_summary.csv
"""
from pathlib import Path
import re
import pandas as pd

MIN_CELLS = 500
RESULTS = Path(__file__).resolve().parents[1] / "results"

frames = []
for f in sorted(RESULTS.glob("Kif13a_WMB-10Xv3-*_subclass_summary.csv")):
    region = re.search(r"WMB-10Xv3-(.+)_subclass_summary", f.name).group(1)
    d = pd.read_csv(f, keep_default_na=False)
    d["region"] = region
    frames.append(d)

a = pd.concat(frames, ignore_index=True)
print(f"Partitions: {a.region.nunique()}   cells: {a.n_cells.sum():,}   subclasses: {a.subclass.nunique()}")

a["w"] = a.mean_Kif13a * a.n_cells
a["wf"] = a.fraction_expressing * a.n_cells
g = (a.groupby("subclass", as_index=False)
       .agg(n_cells=("n_cells", "sum"), w=("w", "sum"), wf=("wf", "sum"),
            cell_class=("class", lambda s: s.mode().iat[0]),
            neurotransmitter=("neurotransmitter", lambda s: s.mode().iat[0]),
            n_partitions=("region", "nunique")))
g["mean_Kif13a"] = g.w / g.n_cells
g["fraction_expressing"] = g.wf / g.n_cells

ranked = (g[g.n_cells >= MIN_CELLS]
          .sort_values("mean_Kif13a", ascending=False)
          .drop(columns=["w", "wf"]))

print(f"\nSubclasses with >= {MIN_CELLS} cells: {len(ranked)}")
print("\n--- top 20 ---")
print(ranked.head(20).round(3).to_string(index=False))
print("\n--- bottom 10 ---")
print(ranked.tail(10).round(3).to_string(index=False))

ranked.to_csv(RESULTS / "derived_wholebrain_subclass_ranking.csv", index=False)
print(f"\nSaved: {RESULTS / 'derived_wholebrain_subclass_ranking.csv'}")
