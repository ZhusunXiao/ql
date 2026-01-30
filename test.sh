#!/bin/bash

# Quick Log Self-Test Script (Linux/macOS)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  Quick Log Self-Test"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not installed"
    exit 1
fi

# Run tests
python3 tests/test_ql.py
TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo "[SUCCESS] All tests passed"
else
    echo "[FAILED] Some tests failed"
fi

exit $TEST_RESULT
