#!/bin/bash
# Unit test runner script
# Runs pytest with proper Python path configuration

set -e

cd "$(dirname "$0")"

echo "Running unit tests..."
echo "===================="

# Use system python3 with venv site-packages
PYTHONPATH=$(pwd) /usr/bin/python3 -c "
import sys
sys.path.insert(0, '.venv/lib/python3.12/site-packages')
import pytest
exit(pytest.main(['tests/unit/', '-v', '--tb=short']))
"

echo ""
echo "All unit tests passed!"
