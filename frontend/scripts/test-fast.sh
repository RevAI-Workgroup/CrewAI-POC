#!/bin/bash
# Fast frontend test execution script
# This script runs frontend tests with optimized settings for speed

set -e

echo "🚀 Running fast frontend tests..."

# Set test environment
export NODE_ENV=test
export VITE_ENVIRONMENT=test
export VITE_LOG_LEVEL=error

# Run tests with Vitest in parallel
bun run vitest run \
    --reporter=verbose \
    --threads \
    --pool-options.threads.maxThreads=4 \
    --pool-options.threads.minThreads=1 \
    --no-coverage \
    --run \
    "$@"

echo "✅ Fast frontend tests completed!" 