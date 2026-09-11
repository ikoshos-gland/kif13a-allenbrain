"""Test whether OPC Kif13a expression is more regionally variable than oligodendrocyte.

Checks three claims against the 13-partition whole-brain summary:
  1. mature oligodendrocytes exceed OPC in every partition
  2. the spread of OPC region means is larger than the oligodendrocyte spread
  3. the OPC gradient runs cortical/hippocampal high, hindbrain low

Input : results/Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv
"""
from pathlib import Path
import pandas as pd
from scipy import stats

RESULTS = Path(__file__).resolve().parents[1] / "results"
w = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")

opc = w[w.subclass == "326 OPC NN"].set_index("region").mean_Kif13a
oli = w[w.subclass == "327 Oligo NN"].set_index("region").mean_Kif13a

print(f"Partitions: {w.region.nunique()}")

cmp = pd.DataFrame({"OPC": opc, "Oligo": oli})
cmp["diff"] = cmp.Oligo - cmp.OPC
print("\n--- per partition ---")
print(cmp.sort_values("diff").round(3).to_string())
print(f"Oligo above OPC in {(cmp['diff'] > 0).sum()} / {len(cmp)} partitions")

print("\n--- spread ---")
for name, s in [("OPC", opc), ("Oligo", oli)]:
    print(f"{name:6s} range={s.max() - s.min():.3f}  SD={s.std(ddof=1):.3f}  "
          f"CV%={100 * s.std(ddof=1) / s.mean():.2f}")

F = opc.var(ddof=1) / oli.var(ddof=1)
p_f = 2 * min(stats.f.cdf(F, len(opc) - 1, len(oli) - 1),
              1 - stats.f.cdf(F, len(opc) - 1, len(oli) - 1))
lev = stats.levene(opc.values, oli.values, center="median")
print(f"variance ratio F={F:.2f} (p={p_f:.2e})   Levene W={lev.statistic:.2f} (p={lev.pvalue:.4f})")

CORTICAL = ["HPF", "Isocortex-1", "Isocortex-2", "CTXsp", "OLF"]
HINDBRAIN = ["P", "MY", "CB"]
print("\n--- cortical/hippocampal vs hindbrain ---")
for name, s in [("OPC", opc), ("Oligo", oli)]:
    r = stats.mannwhitneyu(s[CORTICAL], s[HINDBRAIN], alternative="greater")
    print(f"{name:6s} diff={s[CORTICAL].mean() - s[HINDBRAIN].mean():+.3f} log2   p={r.pvalue:.4f}")

rank = opc.sort_values(ascending=False)
print(f"\ntop 5 = {list(rank.head(5).index)}")
print(f"bottom 3 = {list(rank.tail(3).index)}")
