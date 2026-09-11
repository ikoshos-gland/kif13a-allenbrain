from pathlib import Path
import sys
import pandas as pd

from abc_atlas_access.abc_atlas_cache.abc_project_cache import AbcProjectCache
from abc_atlas_access.abc_atlas_cache.anndata_utils import get_gene_data


# --------------------------------------------------
# 1. Partition argümanı
# --------------------------------------------------
if len(sys.argv) != 2:
    raise SystemExit(
        "Usage: python run_kif13a_partition.py WMB-10Xv3-CTXsp"
    )

partition = sys.argv[1]

if not partition.startswith("WMB-10Xv3-"):
    raise ValueError(f"Unexpected partition: {partition}")

region = partition.replace("WMB-10Xv3-", "")


# --------------------------------------------------
# 2. Dizinler
# --------------------------------------------------
base = Path("/arf/scratch/avural/kif13a_allenbrain")
cache_dir = base / "abc_atlas"
results_dir = base / "results"

results_dir.mkdir(parents=True, exist_ok=True)

print("Partition:", partition)
print("Region:", region)
print("Cache:", cache_dir)
print("Results:", results_dir)


# --------------------------------------------------
# 3. Allen cache
# --------------------------------------------------
abc_cache = AbcProjectCache.from_cache_dir(cache_dir)

print("Manifest:", abc_cache.current_manifest)


# --------------------------------------------------
# 4. Cell metadata
# --------------------------------------------------
cells = abc_cache.get_metadata_dataframe(
    directory="WMB-10X",
    file_name="cell_metadata"
)

cells = cells[
    cells["feature_matrix_label"] == partition
].copy()

print("Selected cells:", len(cells))

if len(cells) == 0:
    raise RuntimeError(f"No cells found for {partition}")

cells = cells.set_index("cell_label")


# --------------------------------------------------
# 5. Gene metadata
# --------------------------------------------------
genes = abc_cache.get_metadata_dataframe(
    directory="WMB-10X",
    file_name="gene"
).set_index("gene_identifier")

kif13a_match = genes[
    genes["gene_symbol"] == "Kif13a"
]

if len(kif13a_match) != 1:
    raise RuntimeError(
        f"Expected exactly one Kif13a gene, found {len(kif13a_match)}"
    )

print("Kif13a gene identifier:", kif13a_match.index[0])


# --------------------------------------------------
# 6. Kif13a expression
# --------------------------------------------------
print("\nLoading Kif13a expression...")

expr = get_gene_data(
    abc_atlas_cache=abc_cache,
    all_cells=cells,
    all_genes=genes,
    selected_genes=["Kif13a"],
    data_type="log2",
    chunk_size=8192
)

print("Expression shape:", expr.shape)

if len(expr) != len(cells):
    raise RuntimeError(
        f"Cell count mismatch: cells={len(cells)}, expression={len(expr)}"
    )


# --------------------------------------------------
# 7. Cell metadata + expression
# --------------------------------------------------
result = cells.join(
    expr,
    how="inner"
).reset_index()

print("Joined shape:", result.shape)


# --------------------------------------------------
# 8. Taxonomy
# --------------------------------------------------
taxonomy = abc_cache.get_metadata_dataframe(
    directory="WMB-taxonomy",
    file_name="cluster_to_cluster_annotation_membership_pivoted",
    keep_default_na=False
)

annotated = result.merge(
    taxonomy,
    on="cluster_alias",
    how="left",
    validate="many_to_one"
)

missing_taxonomy = annotated["cluster"].isna().sum()

print("Annotated shape:", annotated.shape)
print("Missing taxonomy:", missing_taxonomy)

if missing_taxonomy != 0:
    raise RuntimeError(
        f"{missing_taxonomy} cells have missing taxonomy"
    )


# --------------------------------------------------
# 9. Annotated cell-level output
# --------------------------------------------------
annotated_file = (
    results_dir /
    f"Kif13a_{partition}_annotated.csv"
)

annotated.to_csv(
    annotated_file,
    index=False
)

print("Saved:", annotated_file)


# --------------------------------------------------
# 10. Cluster summary
# --------------------------------------------------
cluster_summary = (
    annotated
    .groupby(
        [
            "cluster_alias",
            "cluster",
            "supertype",
            "subclass",
            "class",
            "neurotransmitter"
        ],
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

cluster_file = (
    results_dir /
    f"Kif13a_{partition}_cluster_summary.csv"
)

cluster_summary.to_csv(
    cluster_file,
    index=False
)

print("Saved:", cluster_file)


# --------------------------------------------------
# 11. Subclass summary
# --------------------------------------------------
subclass_summary = (
    annotated
    .groupby(
        [
            "subclass",
            "class",
            "neurotransmitter"
        ],
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

subclass_file = (
    results_dir /
    f"Kif13a_{partition}_subclass_summary.csv"
)

subclass_summary.to_csv(
    subclass_file,
    index=False
)

print("Saved:", subclass_file)


# --------------------------------------------------
# 12. Final QC
# --------------------------------------------------
print("\n=== COMPLETE ===")
print("Partition:", partition)
print("Cells:", len(annotated))
print("Mean Kif13a:", annotated["Kif13a"].mean())
print("Median Kif13a:", annotated["Kif13a"].median())
print(
    "Fraction expressing:",
    (annotated["Kif13a"] > 0).mean()
)
