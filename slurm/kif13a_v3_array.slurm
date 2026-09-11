#!/bin/bash

#SBATCH --job-name=kif13a_v3
#SBATCH --partition=barbun
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --array=0-11%2
#SBATCH --output=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_%A_%a.out
#SBATCH --error=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_%A_%a.err

set -euo pipefail

BASE=/arf/scratch/avural/kif13a_allenbrain
PARTITION_FILE="$BASE/scripts/v3_partitions_remaining.txt"

PARTITION=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$PARTITION_FILE")

if [[ -z "$PARTITION" ]]; then
    echo "ERROR: No partition for array task $SLURM_ARRAY_TASK_ID"
    exit 1
fi

echo "========================================"
echo "SLURM Job ID       : $SLURM_JOB_ID"
echo "Array Job ID       : $SLURM_ARRAY_JOB_ID"
echo "Array Task ID      : $SLURM_ARRAY_TASK_ID"
echo "Node               : $(hostname)"
echo "Partition dataset  : $PARTITION"
echo "Start              : $(date)"
echo "========================================"

source /arf/home/avural/miniconda3/etc/profile.d/conda.sh
conda activate allenbrain

echo
echo "Python:"
which python
python --version

cd "$BASE"

echo
echo "Starting analysis for $PARTITION"

python scripts/run_kif13a_partition.py "$PARTITION"

echo
echo "========================================"
echo "COMPLETED: $PARTITION"
echo "End: $(date)"
echo "========================================"
