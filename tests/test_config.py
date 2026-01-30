"""
Test Configuration File

Used to verify various log2json.py features:
- Basic string matching
- Function-generated cursor
- Lambda-generated layer
- Dynamic subclassname
"""

import re

# ===== Primary Category Name =====
classname = "Test Category"


# ===== Helper Functions =====
def extract_item_number(line, match=None):
    """Extract item number from log line."""
    m = re.search(r'item (\d+)', line)
    return f"ITEM_{m.group(1)}" if m else "ITEM_X"


def get_log_level(line):
    """Get log level."""
    m = re.search(r'\s([EWID])\s', line)
    return m.group(1) if m else 'I'


def dynamic_subclass(line, match=None):
    """Dynamically generate subclassname based on content."""
    if ' E ' in line:
        return "Error Events"
    elif ' W ' in line:
        return "Warning Events"
    else:
        return "General Events"


# ===== Secondary Category Configuration =====
subclasses = [
    {
        # Test 1: Basic static configuration
        "subclassname": "Module Init",
        "rules": [
            {
                "pattern": "TestModule.*initialization",
                "cursor": "INIT_START",
                "layer": 1
            },
            {
                "pattern": "TestModule.*Configuration loaded",
                "cursor": "CONFIG_LOADED",
                "layer": 2
            }
        ]
    },
    {
        # Test 2: Function-generated cursor
        "subclassname": "Data Processing",
        "rules": [
            {
                "pattern": "TestModule.*Processing item",
                "cursor": extract_item_number,
                "layer": 3
            }
        ]
    },
    {
        # Test 3: Lambda-generated layer
        "subclassname": "Connection Management",
        "rules": [
            {
                "pattern": "TestModule.*(connection|Connection)",
                "cursor": "CONNECTION",
                "layer": lambda line, match: 1 if ' E ' in line else 2
            }
        ]
    },
    {
        # Test 4: Dynamic subclassname
        "subclassname": dynamic_subclass,
        "rules": [
            {
                "pattern": "TestModule.*(deprecated|Warning|Error)",
                "cursor": lambda line, match: "ERR" if ' E ' in line else ("WARN" if ' W ' in line else "INFO"),
                "layer": lambda line, match: 1 if ' E ' in line else (2 if ' W ' in line else 3)
            }
        ]
    }
]
