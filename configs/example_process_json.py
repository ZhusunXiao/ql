"""
Example: Using process_json callback to modify JSON after all rules are processed

This is useful when:
- Multiple rules run in parallel and you need to adjust layers based on relationships
- You want to add computed fields based on all matched points
- You need to reorder or filter points after collection

The process_json function receives the complete result JSON and should return 
the modified JSON. Multiple configs can have their own process_json, and they 
will be called in order after all configs are processed.
"""

# ===== Primary Category Name =====
classname = "Example Module"


# ===== Secondary Category Configuration =====
subclasses = [
    {
        "subclassname": "Example Events",
        "rules": [
            {
                "pattern": "example_pattern",
                "cursor": "EXAMPLE",
                "layer": 1
            }
        ]
    }
]


# ===== Post-processing Callback =====
def process_json(result):
    """
    Process the complete JSON result after all rules have been matched.
    
    Args:
        result: Complete JSON structure with format:
            {
                "name": "...",
                "all": [
                    {
                        "classname": "...",
                        "subclasses": [
                            {
                                "subclassname": "...",
                                "points": [
                                    {"timestamp": ..., "cursor": "...", "msg": "...", "line": ..., "layer": ...},
                                    ...
                                ]
                            }
                        ]
                    }
                ]
            }
    
    Returns:
        Modified result JSON
    
    Examples:
        1. Adjust layer based on timestamp order
        2. Add relationship between points from different classes
        3. Compute duration between start/end events
    """
    
    # Example 1: Reassign layers based on timestamp order within each subclass
    for class_data in result.get('all', []):
        for subclass in class_data.get('subclasses', []):
            points = subclass.get('points', [])
            # Sort by timestamp
            points.sort(key=lambda p: p.get('timestamp', 0))
            # Assign layers: first 1/3 -> layer 1, middle 1/3 -> layer 2, last 1/3 -> layer 3
            n = len(points)
            for i, point in enumerate(points):
                if i < n // 3:
                    point['layer'] = 1
                elif i < 2 * n // 3:
                    point['layer'] = 2
                else:
                    point['layer'] = 3
    
    # Example 2: Find pairs of START/END events and mark them with same layer
    # start_events = {}
    # for class_data in result.get('all', []):
    #     for subclass in class_data.get('subclasses', []):
    #         for point in subclass.get('points', []):
    #             cursor = point.get('cursor', '')
    #             if cursor.endswith('_START'):
    #                 key = cursor.replace('_START', '')
    #                 start_events[key] = point
    #             elif cursor.endswith('_END'):
    #                 key = cursor.replace('_END', '')
    #                 if key in start_events:
    #                     # Mark both with same layer
    #                     start_events[key]['layer'] = 1
    #                     point['layer'] = 1
    
    # Example 3: Mark error events with high priority layer
    # for class_data in result.get('all', []):
    #     for subclass in class_data.get('subclasses', []):
    #         for point in subclass.get('points', []):
    #             if 'error' in point.get('msg', '').lower():
    #                 point['layer'] = 1  # High priority
    
    return result
