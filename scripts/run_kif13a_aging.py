from pathlib import Path
import pandas as pd

from abc_atlas_access.abc_atlas_cache.abc_project_cache import AbcProjectCache
from abc_atlas_access.abc_atlas_cache.anndata_utils import get_gene_data


# ============================================================
# PATHS
# ============================================================

BASE = Path("/arf/scratch/avural/kif13a_allenbrain")
CACHE_DIR = BASE / "abc_atlas"
RESULTS_DIR = BASE / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CACHE
# ============================================================

cache = AbcProjectCache.from_cache_dir(CACHE_DIR)

print("Manifest:", cache.current_manifest)


# ============================================================
# 1. CELL METADATA
# ============================================================

print("\n========================================")
print("LOADING AGING MOUSE CELL METADATA")
print("========================================")

cell = cache.get_metadata_dataframe(
    directory="Zeng-Aging-Mouse-10Xv3",
    file_name="cell_metadata"
)

cell["cell_label"] = cell["cell_label"].astype(str)
cell = cell.set_index("cell_label")

print("Total cells:", len(cell))

print("\nAge categories:")
print(cell["donor_age_category"].value_counts(dropna=False))

print("\nUnique donors per age category:")
print(
    cell.groupby("donor_age_category")["donor_label"]
    .nunique()
)

print("\nSex:")
print(cell["donor_sex"].value_counts(dropna=False))


# ============================================================
# 2. TAXONOMY
# ============================================================

print("\n========================================")
print("LOADING CELL-TYPE ANNOTATIONS")
print("========================================")

taxonomy = cache.get_metadata_dataframe(
    directory="Zeng-Aging-Mouse-WMB-taxonomy",
    file_name="cell_cluster_mapping_annotations"
)

taxonomy["cell_label"] = taxonomy["cell_label"].astype(str)
taxonomy = taxonomy.set_index("cell_label")

annotation_cols = [
    "cluster_name",
    "class_name",
    "subclass_name",
    "supertype_name"
]

cell = cell.join(
    taxonomy[annotation_cols],
    how="left"
)

print("Missing subclass annotations:",
      cell["subclass_name"].isna().sum())

print("Missing class annotations:",
      cell["class_name"].isna().sum())


# ============================================================
# 3. GENE METADATA
# ============================================================

print("\n========================================")
print("LOADING GENE METADATA")
print("========================================")

genes = cache.get_metadata_dataframe(
    directory="WMB-10X",
    file_name="gene"
)

genes = genes.set_index("gene_identifier")

kif = genes[
    genes["gene_symbol"].astype(str).str.casefold() == "kif13a"
]

print("\nKif13a:")
print(kif)

if len(kif) != 1:
    raise RuntimeError(
        f"Expected exactly one Kif13a gene; found {len(kif)}"
    )


# ============================================================
# 4. GET KIF13A EXPRESSION
# ============================================================

print("\n========================================")
print("LOADING KIF13A EXPRESSION")
print("========================================")

print(
    "NOTE: On the first run the Aging Mouse log2 "
    "expression matrix may be downloaded."
)

expr = get_gene_data(
    abc_atlas_cache=cache,
    all_cells=cell,
    all_genes=genes,
    selected_genes=["Kif13a"],
    data_type="log2",
    chunk_size=8192
)

print("Expression matrix shape:", expr.shape)


# ============================================================
# 5. ANNOTATED KIF13A TABLE
# ============================================================

keep_cols = [
    "donor_label",
    "donor_age",
    "donor_age_category",
    "donor_sex",
    "region_of_interest_label",
    "anatomical_division_label",
    "population_sampling",
    "feature_matrix_label",
    "cluster_alias",
    "class_name",
    "subclass_name",
    "supertype_name",
    "cluster_name",
    "abc_sample_id"
]

keep_cols = [
    col for col in keep_cols
    if col in cell.columns
]

result = cell[keep_cols].join(
    expr[["Kif13a"]],
    how="inner"
)

# Keep only the two age groups of interest
result = result[
    result["donor_age_category"].isin(["adult", "aged"])
].copy()

result["Kif13a_detected"] = result["Kif13a"] > 0

print("\nAnnotated cells:", len(result))

print("\nOverall Kif13a:")
print(result["Kif13a"].describe())


annotated_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_annotated.csv"
)

result.to_csv(annotated_file)

print("\nSaved:")
print(annotated_file)


# ============================================================
# SUMMARY FUNCTION
# ============================================================

def summarize(df, groups):
    return (
        df.groupby(
            groups,
            observed=True,
            dropna=False
        )
        .agg(
            n_cells=("Kif13a", "size"),
            n_donors=("donor_label", "nunique"),
            mean_Kif13a=("Kif13a", "mean"),
            median_Kif13a=("Kif13a", "median"),
            fraction_expressing=(
                "Kif13a_detected",
                "mean"
            )
        )
        .reset_index()
    )


# ============================================================
# 6. ALL SUBCLASSES: ADULT VS AGED
# ============================================================

print("\n========================================")
print("AGE x SUBCLASS")
print("========================================")

age_subclass = summarize(
    result,
    [
        "donor_age_category",
        "class_name",
        "subclass_name"
    ]
)

age_subclass_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_age_subclass_summary.csv"
)

age_subclass.to_csv(
    age_subclass_file,
    index=False
)

print("Saved:", age_subclass_file)


# ============================================================
# 7. IDENTIFY OPC + OLIGO
# ============================================================

subclasses = (
    result["subclass_name"]
    .dropna()
    .astype(str)
    .unique()
)

oligo_subclasses = sorted(
    [
        x for x in subclasses
        if ("OPC NN" in x or "Oligo NN" in x)
    ]
)

print("\n========================================")
print("OLIGODENDROGLIAL SUBCLASSES FOUND")
print("========================================")

for x in oligo_subclasses:
    print(x)

if len(oligo_subclasses) == 0:
    raise RuntimeError(
        "Could not identify OPC/Oligo subclasses."
    )

oligo_cells = result[
    result["subclass_name"].isin(oligo_subclasses)
].copy()

print("\nTotal OPC/Oligo cells:", len(oligo_cells))


# ============================================================
# 8. OPC / OLIGO: CELL-LEVEL DESCRIPTIVE SUMMARY
# ============================================================

oligo_age = summarize(
    oligo_cells,
    [
        "donor_age_category",
        "class_name",
        "subclass_name"
    ]
)

oligo_age_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_OPC_Oligo_age_summary.csv"
)

oligo_age.to_csv(
    oligo_age_file,
    index=False
)

print("\n========================================")
print("KIF13A: OPC / OLIGO — ADULT VS AGED")
print("========================================")

print(
    oligo_age
    .sort_values(
        ["subclass_name", "donor_age_category"]
    )
    .to_string(index=False)
)

print("\nSaved:")
print(oligo_age_file)


# ============================================================
# 9. DONOR-LEVEL OPC / OLIGO
#
# Important:
# individual cells are NOT treated as biological replicates.
# Each mouse/donor gets its own summary.
# ============================================================

donor_oligo = (
    oligo_cells.groupby(
        [
            "donor_label",
            "donor_age_category",
            "donor_age",
            "donor_sex",
            "class_name",
            "subclass_name"
        ],
        observed=True,
        dropna=False
    )
    .agg(
        n_cells=("Kif13a", "size"),
        mean_Kif13a=("Kif13a", "mean"),
        median_Kif13a=("Kif13a", "median"),
        fraction_expressing=(
            "Kif13a_detected",
            "mean"
        )
    )
    .reset_index()
)

donor_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv"
)

donor_oligo.to_csv(
    donor_file,
    index=False
)

print("\nSaved donor-level table:")
print(donor_file)


# ============================================================
# 10. DONOR-LEVEL AGE COMPARISON
# ============================================================

donor_comparison = (
    donor_oligo.groupby(
        [
            "donor_age_category",
            "subclass_name"
        ],
        observed=True,
        dropna=False
    )
    .agg(
        n_donors=("donor_label", "nunique"),
        total_cells=("n_cells", "sum"),
        mean_of_donor_means=("mean_Kif13a", "mean"),
        median_of_donor_means=("mean_Kif13a", "median"),
        mean_fraction_expressing=(
            "fraction_expressing",
            "mean"
        )
    )
    .reset_index()
)

donor_comparison_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_OPC_Oligo_donor_age_comparison.csv"
)

donor_comparison.to_csv(
    donor_comparison_file,
    index=False
)

print("\n========================================")
print("DONOR-LEVEL AGE COMPARISON")
print("========================================")

print(
    donor_comparison
    .sort_values(
        ["subclass_name", "donor_age_category"]
    )
    .to_string(index=False)
)

print("\nSaved:")
print(donor_comparison_file)


# ============================================================
# 11. REGION x AGE x OPC/OLIGO
# ============================================================

region_oligo = summarize(
    oligo_cells,
    [
        "donor_age_category",
        "anatomical_division_label",
        "subclass_name"
    ]
)

region_oligo_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv"
)

region_oligo.to_csv(
    region_oligo_file,
    index=False
)

print("\nSaved region table:")
print(region_oligo_file)


# ============================================================
# 12. SIMPLE ADULT-vs-AGED DELTAS
# ============================================================

pivot = oligo_age.pivot(
    index="subclass_name",
    columns="donor_age_category",
    values=[
        "mean_Kif13a",
        "median_Kif13a",
        "fraction_expressing",
        "n_cells",
        "n_donors"
    ]
)

pivot.columns = [
    f"{metric}_{age}"
    for metric, age in pivot.columns
]

pivot = pivot.reset_index()

if (
    "mean_Kif13a_adult" in pivot.columns
    and "mean_Kif13a_aged" in pivot.columns
):
    pivot["delta_mean_aged_minus_adult"] = (
        pivot["mean_Kif13a_aged"]
        - pivot["mean_Kif13a_adult"]
    )

if (
    "median_Kif13a_adult" in pivot.columns
    and "median_Kif13a_aged" in pivot.columns
):
    pivot["delta_median_aged_minus_adult"] = (
        pivot["median_Kif13a_aged"]
        - pivot["median_Kif13a_adult"]
    )

if (
    "fraction_expressing_adult" in pivot.columns
    and "fraction_expressing_aged" in pivot.columns
):
    pivot["delta_fraction_aged_minus_adult"] = (
        pivot["fraction_expressing_aged"]
        - pivot["fraction_expressing_adult"]
    )

delta_file = (
    RESULTS_DIR /
    "Kif13a_AgingMouse_OPC_Oligo_adult_vs_aged.csv"
)

pivot.to_csv(
    delta_file,
    index=False
)

print("\n========================================")
print("ADULT vs AGED DELTA")
print("========================================")

print(pivot.to_string(index=False))

print("\nSaved:")
print(delta_file)


# ============================================================
# DONE
# ============================================================

print("\n========================================")
print("FINISHED KIF13A AGING ANALYSIS")
print("========================================")
