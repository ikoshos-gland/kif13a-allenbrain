# Results

Small summary tables committed for reproducibility. Files are grouped as follows.

## Whole mouse brain reference atlas (WMB-10Xv3)

- `Kif13a_WMB-10Xv3-<PARTITION>_subclass_summary.csv` — per-partition mean, median and
  fraction expressing for every cell subclass.
- `Kif13a_WMB-10Xv3-<PARTITION>_cluster_summary.csv` — the same at cluster resolution.
- `Kif13a_WMB-10Xv3-<PARTITION>_subclass_robust*.csv` — early exploratory variants,
  kept only for provenance.
- `Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv` — OPC and oligodendrocyte
  values pooled across all 13 partitions.

## Aging cohort (Zeng Aging Mouse 10Xv3)

- `Kif13a_AgingMouse_age_subclass_summary.csv` — age category by subclass.
- `Kif13a_AgingMouse_OPC_Oligo_age_summary.csv` — adult vs aged, pooled cells.
- `Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv` — one row per mouse per subclass.
- `Kif13a_AgingMouse_OPC_Oligo_donor_age_comparison.csv` — donor means by age group.
- `Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv` — age group by anatomical division.
- `Kif13a_AgingMouse_OPC_Oligo_adult_vs_aged.csv` — the adult/aged deltas.
- `Kif13a_AgingMouse_Allen_ageDE.csv` — **header only**. Kif13a does not appear in
  Allen's published age differential expression table, so the query returned nothing.

## Derived (written by scripts under `analysis/`)

- `derived_donor_level_age_test.csv`
- `derived_wholebrain_subclass_ranking.csv`

Tables above ~2 MB are excluded by `.gitignore`; regenerate them by rerunning the pipeline.
