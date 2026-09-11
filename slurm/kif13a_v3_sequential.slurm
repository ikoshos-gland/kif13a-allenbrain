#!/bin/bash

#SBATCH --job-name=kif13a_v3_seq
#SBATCH --partition=barbun
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_v3_seq_%j.out
#SBATCH --error=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_v3_seq_%j.err

set -euo pipefail

BASE=/arf/scratch/avural/kif13a_allenbrain
PARTITION_FILE="$BASE/scripts/v3_partitions_remaining.txt"

source /arf/home/avural/miniconda3/etc/profile.d/conda.sh
conda activate allenbrain

cd "$BASE"

echo "=== JOB INFO ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo

while read -r PARTITION; do
    [[ -z "$PARTITION" ]] && continue

    echo "========================================"
    echo "STARTING: $PARTITION"
    echo "Time: $(date)"
    echo "========================================"

    python scripts/run_kif13a_partition.py "$PARTITION"

    echo
    echo "FINISHED: $PARTITION"
    echo "Time: $(date)"
    echo
done < "$PARTITION_FILE"

echo "=== ALL PARTITIONS COMPLETE ==="
echo "End: $(date)"
