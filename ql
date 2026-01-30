#!/bin/bash

# ql - Quick Log Analysis Tool
# Usage: ql <log_file> [config_pattern]
# Examples:
#   ql aaa.log
#   ql aaa.log audio.py
#   ql log/1.log "configs/*.py"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: ql <log_file> [config_pattern]"
    echo ""
    echo "Examples:"
    echo "  ql aaa.log              Use configs/*.py to analyze log"
    echo "  ql aaa.log audio.py     Use only audio.py config"
    echo "  ql log/1.log            Analyze log in log directory"
    exit 1
fi

LOG_FILE="$1"
CONFIG_PATTERN="${2:-configs/*.py}"

# Get log file name without path and extension
LOG_NAME=$(basename "$LOG_FILE" | sed 's/\.[^.]*$//')

# Output file paths
JSON_FILE="output/${LOG_NAME}.json"
HTML_FILE="output/${LOG_NAME}.html"

# Ensure output directory exists
mkdir -p output

echo ""
echo "========================================"
echo "  ql - Quick Log"
echo "========================================"
echo ""
echo "[LOG]    $LOG_FILE"
echo "[CONFIG] $CONFIG_PATTERN"
echo "[OUTPUT] $HTML_FILE"
echo ""

# Step 1: Log -> JSON
echo "[1/2] Extracting log data..."
python3 "$SCRIPT_DIR/log2json.py" "$LOG_FILE" $CONFIG_PATTERN -o "$JSON_FILE"
if [ $? -ne 0 ]; then
    echo "[ERROR] log2json failed"
    exit 1
fi

# Step 2: JSON -> HTML
echo ""
echo "[2/2] Generating HTML..."
python3 "$SCRIPT_DIR/json2html.py" "$JSON_FILE" "$HTML_FILE"
if [ $? -ne 0 ]; then
    echo "[ERROR] json2html failed"
    exit 1
fi

echo ""
echo "========================================"
echo "[DONE] $HTML_FILE"
echo "========================================"
echo ""

# Try to auto-open HTML file
if command -v xdg-open &> /dev/null; then
    xdg-open "$HTML_FILE" 2>/dev/null &
elif command -v open &> /dev/null; then
    open "$HTML_FILE" 2>/dev/null &
fi
