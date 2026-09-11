"""Check whether the regional Kif13a pattern replicates in an independent cohort.

The whole-brain reference atlas and the aging cohort are different mice from
different experiments. If the regional ordering agrees across both, the pattern
is unlikely to be a batch artefact of either one.

Only the 7 anatomical divisions sampled by the aging study are comparable.
Isocortex-1 and Isocortex-2 are pooled back into one division, weighted by cell count.

Inputs : results/Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv
         results/Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv
"""
from pathlib import Path
import pandas as pd
from scipy import stats

RESULTS = Path(__file__).resolve().parents[1] / "results"
w = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
a = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv")

w["division"] = w.region.replace({"Isocortex-1": "Isocortex", "Isocortex-2": "Isocortex"})
w["prod"] = w.mean_Kif13a * w.n_cells
wm = w.groupby(["division", "subclass"], as_index=False).agg(prod=("prod", "sum"), n=("n_cells", "sum"))
wm["reference_mean"] = wm["prod"] / wm["n"]

adult = (a[a.donor_age_category == "adult"]
         .rename(columns={"anatomical_division_label": "division",
                          "subclass_name": "subclass",
                          "mean_Kif13a": "aging_mean"})
         [["division", "subclass", "aging_mean"]])

merged = wm.merge(adult, on=["division", "subclass"])
print(f"Shared divisions: {merged['division'].nunique()} -> {sorted(merged['division'].unique())}")

for sc, label in [("326 OPC NN", "OPC"), ("327 Oligo NN", "Oligo")]:
    s = merged[merged.subclass == sc].sort_values("reference_mean", ascending=False)
    rho, p_s = stats.spearmanr(s.reference_mean, s.aging_mean)
    r, p_p = stats.pearsonr(s.reference_mean, s.aging_mean)
    print(f"\n--- {label} (n={len(s)} divisions) ---")
    print(s[["division", "reference_mean", "aging_mean"]].round(3).to_string(index=False))
    print(f"Spearman rho={rho:+.3f} (p={p_s:.4f})   Pearson r={r:+.3f} (p={p_p:.4f})")
