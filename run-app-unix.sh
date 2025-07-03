#!/bin/bash

# Save diagnostic logs
exec > /var/log/workload_t3rn.log 2>&1

echo "$(date): Starting T3RN workload..."
echo "Current directory before change: $(pwd)"

# Change to project directory
cd /root/dev/Workloads/WRKLD_T3RN
echo "Current directory after change: $(pwd)"

echo "Activating virtualenv..."
# Activate virtual environment
source /root/dev/Workloads/WRKLD_T3RN/venv/bin/activate

echo "Checking environment..."
which python3
python3 --version
pip list | grep python-dotenv

echo "Starting workload..."
# Run the workload directly
python3 workload_t3rn.py
