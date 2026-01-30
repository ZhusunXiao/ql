"""
Audio Subsystem Configuration

Configuration file structure:
- classname: Primary category name
- subclasses: List of secondary categories, each containing:
    - subclassname: String or function (line, match) -> str
    - rules: List of rules
        - pattern: ripgrep regex pattern
        - cursor: String or function (line, match) -> str
        - layer: Integer or function (line, match) -> int
"""

import re

# ===== Primary Category Name =====
classname = "Audio Subsystem"


# ===== Helper Functions =====
def extract_function_name(line):
    """Extract function name from log line"""
    match = re.search(r':(\w+):', line)
    return match.group(1) if match else None


def get_log_level(line):
    """Get log level E/W/I/D"""
    match = re.search(r'\s([EWID])\s', line)
    return match.group(1) if match else 'I'


def level_to_layer(line, match=None):
    """Determine layer based on log level"""
    level = get_log_level(line)
    return {'E': 1, 'W': 2, 'I': 2, 'D': 3}.get(level, 2)


# ===== Secondary Category Configuration =====
subclasses = [
    {
        "subclassname": "ADSP Initialization",
        "rules": [
            {
                "pattern": "DMABUFHEAPS",
                "cursor": "DMABUF_INIT",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*fastrpc_apps_user_init done",
                "cursor": "FASTRPC_INIT_DONE",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*libadsprpc.so loaded",
                "cursor": "ADSPRPC_LOADED",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*set up allocator",
                "cursor": "RPCMEM_SETUP",
                "layer": 2
            },
            {
                "pattern": "audioadsprpcd.*Reading configuration",
                "cursor": "CONFIG_READ",
                "layer": 2
            }
        ]
    },
    {
        "subclassname": "ADSP Errors",
        "rules": [
            {
                "pattern": "audioadsprpcd.*Error.*open_device_node",
                "cursor": "ERR_OPEN_DEVICE",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*Error.*apps_dev_init",
                "cursor": "ERR_DEV_INIT",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*Error.*remote_handle_open",
                "cursor": "ERR_REMOTE_HANDLE",
                "layer": 1
            },
            {
                "pattern": "audioadsprpcd.*will restart",
                "cursor": "DAEMON_RESTART",
                "layer": 2
            }
        ]
    },
    {
        "subclassname": "Domain Management",
        "rules": [
            {
                "pattern": "audioadsprpcd.*domain_deinit",
                # Use function to dynamically generate cursor
                "cursor": lambda line, match: "DOMAIN_DEINIT_" + (re.search(r'domain (\d+)', line).group(1) if re.search(r'domain (\d+)', line) else "X"),
                "layer": 3
            }
        ]
    },
    {
        "subclassname": "Log Level Example",
        "rules": [
            {
                "pattern": "AudioFlinger.*start|stop",
                "cursor": "AUDIO_FLINGER",
                # Use lambda to dynamically generate layer: Error=1, Warning=2, other=3
                "layer": lambda line, match: 1 if ' E ' in line else (2 if ' W ' in line else 3)
            },
            {
                "pattern": "AudioPolicy.*output",
                "cursor": "AUDIO_POLICY",
                # Can also call a defined function
                "layer": level_to_layer
            }
        ]
    }
]
