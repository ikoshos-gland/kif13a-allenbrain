from pathlib import Path
import pandas as pd

BASE = Path("/arf/scratch/avural/kif13a_allenbrain")
RESULTS = BASE / "results"

files = sorted(RESULTS.glob("Kif13a_WMB-10Xv3-*_annotated.csv"))

print("Found annotated files:", len(files))

rows = []

for f in files:
    region = f.name.replace("Kif13a_WMB-10Xv3-", "").replace("_annotated.csv", "")

    print("Reading:", region)

    df = pd.read_csv(f, keep_default_na=False)

    # Focus on OPC and mature oligodendrocytes
    sub = df[
        df["subclass"].isin([
            "326 OPC NN",
            "327 Oligo NN"
        ])
    ].copy()

    summary = (
        sub.groupby(
            ["subclass", "class"],
            observed=True,
            dropna=False
        )
        .agg(
            n_cells=("Kif13a", "size"),
            mean_Kif13a=("Kif13a", "mean"),
            median_Kif13a=("Kif13a", "median"),
            fraction_expressing=(
                "Kif13a",
                lambda x: (x > 0).mean()
            )
        )
        .reset_index()
    )

    summary["region"] = region

    rows.append(summary)

out = pd.concat(rows, ignore_index=True)

out = out[
    [
        "region",
        "subclass",
        "class",
        "n_cells",
        "mean_Kif13a",
        "median_Kif13a",
        "fraction_expressing"
    ]
]

out = out.sort_values(
    ["subclass", "mean_Kif13a"],
    ascending=[True, False]
)

outfile = RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv"
out.to_csv(outfile, index=False)

print("\n========================================")
print("OPC / OLIGO ACROSS ALL 13 REGIONS")
print("========================================")

print(out.to_string(index=False))

print("\nSaved:")
print(outfile)
