# Kif13a across the mouse brain and across age

Single-cell RNA sequencing analysis of one gene, `Kif13a` (ENSMUSG00000021375), across the
Allen Brain Cell Atlas. Two questions are asked: which cell types express it, and whether
that expression changes between young adult and aged mice.

All compute ran on TRUBA, the Turkish national HPC centre, under SLURM.

## Findings

**Kif13a is an oligodendroglial gene, not a general glial gene.** Across 2,341,350 cells and
265 sufficiently sampled subclasses, mature oligodendrocytes rank first and their precursors
second. Astrocytes, microglia and endothelial cells sit roughly sixteen-fold lower, so the
signal does not simply track "glia".

| Cell type | Mean log2 | Fraction expressing |
|---|---|---|
| Mature oligodendrocyte | 7.77 | 0.93 |
| OPC (precursor) | 6.76 | 0.85 |
| Astrocyte (telencephalic) | 3.77 | 0.51 |
| Microglia | 3.88 | 0.49 |
| Pericyte | 2.85 | 0.35 |

**Precursors vary by region, mature cells do not.** Oligodendrocyte expression is flat across
the brain, while OPC expression spans a range roughly three times wider, highest in
hippocampal and cortical partitions and lowest in cerebellum and medulla. The variance
difference is significant (Levene p < 0.0001) and the ordering replicates in the independent
aging cohort (Spearman rho = +0.96 across the 7 shared divisions).

**Expression rises with age in mature oligodendrocytes only.** Comparing 53 young adult mice
(~2 months) against 44 aged mice (~18 months), collapsed to one value per mouse:

| Subclass | Delta (log2) | Fold change | Mann-Whitney p | Cliff's delta |
|---|---|---|---|---|
| Mature oligodendrocyte | +0.250 | 1.19 | 0.0002 | +0.435 |
| OPC | +0.131 | 1.09 | 0.22 | +0.146 |

The fraction of cells expressing the gene is unchanged, so already-expressing cells shift
upward rather than more cells switching on. Note that `Kif13a` does not appear in Allen's own
published age differential expression table, meaning the effect is real but modest.

## Data

Both datasets come from the Allen Brain Cell Atlas via `abc-atlas-access`, release `20260711`.
They share one taxonomy: 34 classes, 338 subclasses, 1,201 supertypes, 5,322 clusters.

| | Reference atlas | Aging cohort |
|---|---|---|
| Name | WMB-10Xv3 | Zeng Aging Mouse 10Xv3 |
| Cells | 2,341,350 | 1,162,565 |
| Partitions | 13 | 7 divisions |
| Donors | not extracted | 108 (64 adult, 44 aged) |
| Matrices on disk | ~95 GB | ~13 GB |

Expression values are `log2(CPM + 1)`. The aging cohort covers isocortex, hippocampal
formation, midbrain, pallidum, hypothalamus, pons and striatum. It does **not** include
cerebellum, medulla, thalamus, olfactory areas or cortical subplate, so the age result is
untested in exactly the regions where OPC expression is lowest.

The atlas cache is not committed. Scripts download it on first run.

## Layout

```
scripts/    analysis code that runs on the cluster
slurm/      SLURM submission scripts
analysis/   post-hoc statistics, runnable locally from the committed results
results/    small summary tables (see results/README.md)
```

### Cluster pipeline

| File | Purpose |
|---|---|
| `scripts/run_kif13a_partition.py` | Pulls Kif13a from one anatomical partition, joins cell-type annotations, writes per-subclass and per-cluster summaries. |
| `scripts/run_kif13a_aging.py` | The aging comparison. Loads the aging cohort, groups by age category, and writes cell-level, donor-level and region-level tables. |
| `scripts/summarize_kif13a_all_regions.py` | Pools OPC and oligodendrocyte values across all 13 partitions. |
| `scripts/check_kif13a_aging_de.py` | Queries Allen's published age differential expression table for Kif13a. |

### Post-hoc analysis

These read only the committed tables, so they run anywhere with `pandas` and `scipy`.

| File | Purpose |
|---|---|
| `analysis/donor_level_age_test.py` | Collapses each mouse to one value, then tests adult against aged. The cluster pipeline reports means without a significance test; testing per cell would treat thousands of cells from one mouse as independent. |
| `analysis/regional_heterogeneity.py` | Tests whether OPC expression is more regionally variable than oligodendrocyte expression. |
| `analysis/cross_dataset_replication.py` | Correlates the regional ordering between the two independent cohorts. |
| `analysis/wholebrain_subclass_ranking.py` | Builds the whole-brain ranking of all subclasses. |

## Running it

On the cluster, edit the paths at the top of each script to your own scratch directory, then:

```bash
sbatch slurm/kif13a_v3_sequential.slurm   # all reference atlas partitions
sbatch slurm/kif13a_aging.slurm           # the aging comparison
```

Locally, against the committed tables:

```bash
pip install -r requirements.txt
python analysis/donor_level_age_test.py
python analysis/regional_heterogeneity.py
python analysis/cross_dataset_replication.py
python analysis/wholebrain_subclass_ranking.py
```

## Limitations

The measurement is mRNA, not protein, so a transcript increase does not establish that
KIF13A protein rises. CPM is a relative unit, so a drop in total mRNA per cell would inflate
the ratio on its own. Sequencing destroys spatial position, so this says how much, never
where. The whole-brain ranking pools cells without a per-donor correction and is descriptive.
The age result rests on one cohort covering 7 of 13 regions.

## Acknowledgment

The numerical calculations reported here were performed at TUBITAK ULAKBIM, High Performance
and Grid Computing Center (TRUBA resources).

Data from the Allen Brain Cell Atlas (Allen Institute for Brain Science).
