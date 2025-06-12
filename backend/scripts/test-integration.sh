#!/bin/bash
# Integration test execution script
# This script runs integration tests that require database and redis

set -e

echo "🔧 Running integration tests..."

# Check if required services are available
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using test database"
    export DATABASE_URL="sqlite:///./test_integration.db"
fi

if [ -z "$REDIS_URL" ]; then
    echo "⚠️  REDIS_URL not set, skipping Redis-dependent tests"
fi

# Set test environment
export TESTING=1
export SECRET_KEY="test-secret-key-for-testing-only"
export ENCRYPTION_KEY="test-encryption-key-32-chars-long!"

# Run integration tests with coverage
pytest \
    -m "integration" \
    --numprocesses=2 \
    --dist=worksteal \
    --tb=line \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=xml \
    "$@"

echo "✅ Integration tests completed!" 