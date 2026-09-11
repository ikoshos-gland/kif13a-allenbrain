#!/bin/bash
#SBATCH --job-name=kif13a_finish
#SBATCH --partition=barbun
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_finish_%j.out
#SBATCH --error=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_finish_%j.err

set -euo pipefail

PYTHON=/arf/home/avural/miniconda3/envs/allenbrain/bin/python
BASE=/arf/scratch/avural/kif13a_allenbrain

cd "$BASE"

echo "========================================"
echo "STARTING: WMB-10Xv3-STR"
echo "========================================"

"$PYTHON" scripts/run_kif13a_partition.py WMB-10Xv3-STR

echo "========================================"
echo "FINISHED: WMB-10Xv3-STR"
echo "========================================"

echo "========================================"
echo "STARTING: WMB-10Xv3-TH"
echo "========================================"

"$PYTHON" scripts/run_kif13a_partition.py WMB-10Xv3-TH

echo "========================================"
echo "FINISHED: WMB-10Xv3-TH"
echo "========================================"

echo "ALL DONE"
