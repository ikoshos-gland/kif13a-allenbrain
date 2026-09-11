#!/bin/bash

#SBATCH --job-name=kif13a_ctxsp_test
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --output=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_ctxsp_test_%j.out
#SBATCH --error=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_ctxsp_test_%j.err

set -euo pipefail

echo "=== JOB INFO ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "Working directory: $(pwd)"

source /arf/home/avural/miniconda3/etc/profile.d/conda.sh
conda activate allenbrain

echo
echo "=== PYTHON ==="
which python
python --version

cd /arf/scratch/avural/kif13a_allenbrain

echo
echo "=== ANALYSIS ==="

python scripts/run_kif13a_partition.py WMB-10Xv3-CTXsp

echo
echo "=== FINISHED ==="
echo "End: $(date)"
