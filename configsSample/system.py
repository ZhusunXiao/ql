"""
System Boot Configuration

Demonstrates advanced function usage
"""

import re

# ===== Primary Category Name =====
classname = "System Boot"


# ===== Helper Functions =====
def extract_property_name(line, match=None):
    """Extract property name from avc denied log as cursor."""
    m = re.search(r'property=([^\s]+)', line)
    if m:
        prop = m.group(1)
        prop_clean = re.sub(r'[^\w]', '_', prop)
        return f"AVC_{prop_clean}"
    return "AVC_UNKNOWN"


def extract_audit_type(line, match=None):
    """Extract type from audit log."""
    m = re.search(r'type=(\d+)', line)
    if m:
        type_code = m.group(1)
        type_names = {
            '2000': 'AUDIT_INIT',
            '1403': 'SELINUX_STATUS',
            '1404': 'SELINUX_ENFORCING',
            '1107': 'AVC_DENIED'
        }
        return type_names.get(type_code, f'AUDIT_{type_code}')
    return "AUDIT_UNKNOWN"


def get_vintf_cursor(line, match=None):
    """Extract VINTF operation name."""
    m = re.search(r'(get\w+Manifest)', line)
    return m.group(1) if m else "VINTF_OP"


def dynamic_subclass_by_content(line, match=None):
    """Dynamically determine subclass name based on log content."""
    if 'enforcing' in line.lower():
        return "SELinux Enforcing"
    elif 'denied' in line.lower():
        return "SELinux Denied"
    else:
        return "SELinux Other"


# ===== Secondary Category Configuration =====
subclasses = [
    {
        # Use function to dynamically generate subclass name
        "subclassname": dynamic_subclass_by_content,
        "rules": [
            {
                "pattern": "SELinux.*Loaded.*context",
                "cursor": "SELINUX_CONTEXT_LOAD",
                "layer": 1
            },
            {
                "pattern": "avc.*denied.*property=",
                "cursor": extract_property_name,
                "layer": 2
            },
            {
                "pattern": "enforcing=1",
                "cursor": "SELINUX_ENFORCING_ON",
                "layer": 1
            }
        ]
    },
    {
        "subclassname": "Audit Log",
        "rules": [
            {
                "pattern": "auditd.*type=",
                "cursor": extract_audit_type,
                "layer": lambda line, match: 1 if 'initialized' in line else 2
            }
        ]
    },
    {
        "subclassname": "Service Manager",
        "rules": [
            {
                "pattern": "hwservicemanager.*VINTF",
                "cursor": get_vintf_cursor,
                "layer": 1
            },
            {
                "pattern": "ServiceManager.*Failed",
                "cursor": "SERVICE_MANAGER_FAIL",
                "layer": 1
            }
        ]
    }
]
