#!/bin/bash

# Quick Log Installation Script (Linux/macOS)

echo ""
echo "========================================"
echo "  Quick Log Installation (Linux/macOS)"
echo "========================================"
echo ""

# Get absolute path of script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Install directory: $SCRIPT_DIR"
echo ""

# Detect shell config file
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.bash_profile" ]; then
        SHELL_RC="$HOME/.bash_profile"
    else
        SHELL_RC="$HOME/.bashrc"
    fi
else
    SHELL_RC="$HOME/.profile"
fi

echo "Shell config: $SHELL_RC"

# Check if already added
if grep -q "quicklog" "$SHELL_RC" 2>/dev/null; then
    echo "[INFO] quicklog is already in PATH config"
else
    # Add to config file
    echo "" >> "$SHELL_RC"
    echo "# quicklog - Log Timeline Analysis Tool" >> "$SHELL_RC"
    echo "export PATH=\"\$PATH:$SCRIPT_DIR\"" >> "$SHELL_RC"
    echo "[OK] Added to $SHELL_RC"
    echo ""
    echo "Run the following command to apply:"
    echo "  source $SHELL_RC"
fi

# Set executable permission
chmod +x "$SCRIPT_DIR/ql" 2>/dev/null

echo ""
echo "========================================"
echo "  Usage:"
echo "  ql <log_file> [config_pattern]"
echo "========================================"
echo ""
