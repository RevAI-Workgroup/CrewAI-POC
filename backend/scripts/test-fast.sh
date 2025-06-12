#!/bin/bash
# Fast test execution script for unit tests only
# This script runs only unit tests with parallel execution for maximum speed

set -e

echo "🚀 Running fast unit tests..."

# Set test environment
export TESTING=1
export DATABASE_URL="sqlite:///./test_fast.db"
export SECRET_KEY="test-secret-key-for-testing-only"
export ENCRYPTION_KEY="test-encryption-key-32-chars-long!"

# Run only unit tests with parallel execution
pytest \
    -m "unit" \
    --numprocesses=auto \
    --dist=worksteal \
    --tb=short \
    --quiet \
    --disable-warnings \
    --no-cov \
    "$@"

echo "✅ Fast unit tests completed!" 