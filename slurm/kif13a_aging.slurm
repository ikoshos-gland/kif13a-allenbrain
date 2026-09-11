#!/bin/bash
#SBATCH --job-name=kif13a_age
#SBATCH --partition=barbun
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_age_%j.out
#SBATCH --error=/arf/scratch/avural/kif13a_allenbrain/logs/kif13a_age_%j.err

set -euo pipefail

PYTHON=/arf/home/avural/miniconda3/envs/allenbrain/bin/python
BASE=/arf/scratch/avural/kif13a_allenbrain

cd "$BASE"

echo "========================================"
echo "KIF13A AGING MOUSE"
echo "Host: $(hostname)"
echo "Started: $(date)"
echo "========================================"

"$PYTHON" scripts/run_kif13a_aging.py

echo "========================================"
echo "FINISHED"
echo "Ended: $(date)"
echo "========================================"
