from pathlib import Path
import pandas as pd

from abc_atlas_access.abc_atlas_cache.abc_project_cache import AbcProjectCache

BASE = Path("/arf/scratch/avural/kif13a_allenbrain")
CACHE_DIR = BASE / "abc_atlas"
RESULTS_DIR = BASE / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

cache = AbcProjectCache.from_cache_dir(CACHE_DIR)

print("Manifest:", cache.current_manifest)

print("\nLoading Allen Aging Mouse age-DE table...")

de = cache.get_metadata_dataframe(
    directory="Zeng-Aging-Mouse-WMB-taxonomy",
    file_name="aging_degenes"
)

print("age-DE table shape:", de.shape)

kif = de[
    de["gene_symbol"].astype(str).str.casefold() == "kif13a"
].copy()

outfile = RESULTS_DIR / "Kif13a_AgingMouse_Allen_ageDE.csv"
kif.to_csv(outfile, index=False)

print("\n====================================")
print("KIF13A AGE-DE RESULTS")
print("====================================")

if len(kif) == 0:
    print(
        "Kif13a is NOT present in Allen's reported significant age-DE table."
    )
    print(
        "This does NOT prove there is zero age difference; "
        "it means Kif13a did not meet the published age-DE reporting criteria "
        "in the tested cell-type groups."
    )
else:
    cols = [
        "grouping_type",
        "grouping_name",
        "age_effect_size",
        "adjusted_pvalue",
        "confidence_interval_lower_bound",
        "confidence_interval_higher_bound"
    ]

    print(
        kif[cols]
        .sort_values("adjusted_pvalue")
        .to_string(index=False)
    )

    print("\nInterpretation:")
    print("  age_effect_size > 0  -> higher with aging")
    print("  age_effect_size < 0  -> lower with aging")

print("\nSaved:")
print(outfile)
