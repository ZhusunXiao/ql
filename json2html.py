#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert JSON to interactive HTML visualization (ECharts version)
Usage: python json2html.py rules.json rules.html
"""

import json
import sys
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from collections import defaultdict
from datetime import datetime
from pathlib import Path


def timestamp_to_str(timestamp):
    """Convert timestamp to readable time string."""
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "N/A"


def timestamp_to_time_with_ms(timestamp):
    """Convert timestamp to HH:MM:SS.mmm format."""
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
        return f'{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{int((timestamp % 1) * 1000):03d}'
    return "N/A"


def generate_html(data, output_file):
    """Generate HTML file from JSON data."""
    
    title = data.get("name", "Timeline Visualization")
    all_items = data.get("all", [])
    
    # Collect all data points and category hierarchy (single traversal)
    all_points = []
    y_axis_categories = []
    category_map = {}
    class_hierarchy = []
    total_classes = 0
    total_subclasses = 0
    total_points = 0
    
    for item in all_items:
        if not item:
            continue
        total_classes += 1
        classname = item.get("classname", "Unnamed")
        subclasses = item.get("subclasses", [])
        
        class_info = {
            'classname': classname,
            'subclasses': []
        }
        
        for subclass in subclasses:
            total_subclasses += 1
            subclassname = subclass.get("subclassname", "Unnamed")
            # Use classname|subclassname as unique category_label for internal matching
            # Y-axis formatter will extract and display only subclassname part
            category_label = f"{classname}|{subclassname}"
            
            if category_label not in category_map:
                category_index = len(y_axis_categories)
                category_map[category_label] = category_index
                y_axis_categories.append(category_label)
            else:
                category_index = category_map[category_label]
            
            class_info['subclasses'].append({
                'subclassname': subclassname,
                'category_label': category_label
            })
            
            points = subclass.get("points", [])
            points_len = len(points)
            total_points += points_len
            
            for point in points:
                timestamp_ms = int(point.get("timestamp", 0))
                timestamp = timestamp_ms * 0.001  # multiplication is faster than division
                
                all_points.append({
                    'timestamp': timestamp,
                    'timestamp_ms': timestamp_ms,
                    'cursor': point.get("cursor", "N/A"),
                    'msg': point.get("msg", ""),
                    'line': point.get("line", "N/A"),
                    'layer': point.get("layer", 1),
                    'classname': classname,
                    'subclassname': subclassname,
                    'category': category_label,
                    'category_index': category_index,
                    'timeStr': timestamp_to_time_with_ms(timestamp)
                })
        
        class_hierarchy.append(class_info)
    
    # Add X-axis offset for events at same millisecond in same category
    all_points.sort(key=lambda x: (x['timestamp_ms'], x['category_index'], x['line']))
    
    # Group by timestamp+category index (using defaultdict for optimization)
    timestamp_category_groups = defaultdict(list)
    for point in all_points:
        timestamp_category_groups[(point['timestamp_ms'], point['category_index'])].append(point)
    
    # Distribute points within ±0.5ms range for each timestamp+category group
    for key, points in timestamp_category_groups.items():
        current_ts = key[0]
        n = len(points)
        
        if n > 1:
            # Distribute within ±0.5ms range (1ms total range)
            # This prevents overlap with adjacent millisecond points
            total_range = 0.9  # Use 0.9ms, leaving some margin
            step = total_range / (n - 1) if n > 1 else 0
            offset_start = -total_range / 2
            
            for i, point in enumerate(points):
                point['display_timestamp_ms'] = current_ts + offset_start + (i * step)
                point['display_y'] = point['category_index']
        else:
            # Single point, no offset needed
            points[0]['display_timestamp_ms'] = points[0]['timestamp_ms']
            points[0]['display_y'] = points[0]['category_index']
    
    # Layer color definitions - array for cycling through many layers
    layer_color_palette = [
        '#667eea',  # Purple-blue
        '#28a745',  # Green
        '#ffc107',  # Yellow
        '#dc3545',  # Red
        '#17a2b8',  # Cyan
        '#fd7e14',  # Orange
        '#6f42c1',  # Purple
        '#20c997',  # Teal
        '#e83e8c',  # Pink
        '#007bff',  # Blue
        '#6610f2',  # Indigo
        '#795548',  # Brown
        '#607d8b',  # Blue-grey
        '#4caf50',  # Light green
        '#ff5722',  # Deep orange
        '#9c27b0',  # Deep purple
        '#00bcd4',  # Light cyan
        '#8bc34a',  # Lime
        '#ff9800',  # Amber
        '#3f51b5',  # Indigo blue
    ]
    
    def get_layer_color(layer: int) -> str:
        """Get color for layer, cycling through palette."""
        return layer_color_palette[(layer - 1) % len(layer_color_palette)]
    
    def get_layer_name(layer: int) -> str:
        """Get display name for layer."""
        return f'Layer {layer}'
    
    # Group by (subclassname, layer) to create series (using defaultdict)
    subclass_layer_series = defaultdict(list)
    for point in all_points:
        layer = point['layer']
        subclassname = point['subclassname']
        subclass_layer_series[(subclassname, layer)].append({
            'value': [point['display_timestamp_ms'], point['display_y'], point['cursor']],
            'cursor': point['cursor'],
            'msg': point['msg'],
            'line': point['line'],
            'layer': layer,
            'classname': point['classname'],
            'subclassname': subclassname,
            'timeStr': point['timeStr']
        })
    
    # Create ECharts series config
    series_config = []
    
    # Sort by subclassname, then by layer
    sorted_keys = sorted(subclass_layer_series.keys())
    
    for (subclassname, layer) in sorted_keys:
        layer_color = get_layer_color(layer)
        layer_name = get_layer_name(layer)
        series_config.append({
            'name': f'{subclassname} - {layer_name}',
            'type': 'scatter',
            'data': subclass_layer_series[(subclassname, layer)],
            'symbolSize': 10,
            'large': True,
            'largeThreshold': 500,
            'itemStyle': {
                'color': layer_color
            },
            'emphasis': {
                'scale': 1.5,
                'itemStyle': {
                    'shadowBlur': 8,
                    'shadowColor': layer_color
                }
            }
        })
    
    # Calculate time range
    if all_points:
        timestamps = [p['display_timestamp_ms'] for p in all_points]
        min_timestamp = min(timestamps)
        max_timestamp = max(timestamps)
    else:
        min_timestamp = max_timestamp = 0
    
    # Prepare chart data
    chart_data = {
        'yAxisData': y_axis_categories,
        'series': series_config,
        'rawData': all_points,
        'classHierarchy': class_hierarchy,
        'minTime': min_timestamp,
        'maxTime': max_timestamp
    }
    
    # Prepare hierarchy JSON (compact format to reduce file size)
    class_hierarchy_json = json.dumps(class_hierarchy, ensure_ascii=False, separators=(',', ':'))
    
    timestamp_str = str(int(time.time()))
    chart_data_json = json.dumps(chart_data, ensure_ascii=False, separators=(',', ':'))
    
    # Extract filename (for localStorage key)
    file_name = Path(output_file).stem.replace("'", "").replace('"', '')
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .main-layout {{
            display: flex;
            gap: 20px;
            max-width: 2000px;
            margin: 0 auto;
        }}
        
        .sidebar {{
            width: 320px;
            flex-shrink: 0;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            max-height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
        }}
        
        .sidebar-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .sidebar-header h3 {{
            font-size: 1.2em;
            margin-bottom: 5px;
        }}
        
        .sidebar-header p {{
            font-size: 0.85em;
            opacity: 0.9;
        }}
        
        .sidebar-actions {{
            padding: 10px 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            gap: 8px;
        }}
        
        .sidebar-actions button {{
            flex: 1;
            padding: 8px 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.3s;
        }}
        
        .btn-select-all {{
            background: #667eea;
            color: white;
        }}
        
        .btn-select-all:hover {{
            background: #5568d3;
        }}
        
        .btn-select-none {{
            background: #dc3545;
            color: white;
        }}
        
        .btn-select-none:hover {{
            background: #c82333;
        }}
        
        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}
        
        .class-group {{
            margin-bottom: 15px;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #e0e0e0;
        }}
        
        .class-header {{
            padding: 12px 15px;
            font-weight: bold;
            font-size: 0.95em;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.3s;
        }}
        
        .class-header:hover {{
            filter: brightness(0.95);
        }}
        
        .class-header .toggle-icon {{
            transition: transform 0.3s;
        }}
        
        .class-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}
        
        .class-color-bar {{
            width: 4px;
            height: 100%;
            position: absolute;
            left: 0;
            top: 0;
        }}
        
        .subclass-list {{
            max-height: 500px;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        
        .subclass-list.collapsed {{
            max-height: 0;
        }}
        
        .subclass-item {{
            padding: 10px 15px 10px 25px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-top: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.2s;
        }}
        
        .subclass-item:hover {{
            background: #f8f9fa;
        }}
        
        .subclass-item input[type="checkbox"] {{
            width: 16px;
            height: 16px;
            cursor: pointer;
        }}
        
        .subclass-item label {{
            flex: 1;
            cursor: pointer;
            font-size: 0.85em;
            color: #333;
            word-break: break-word;
        }}
        
        .subclass-item .point-count {{
            font-size: 0.75em;
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 10px;
            color: #666;
        }}
        
        .container {{
            flex: 1;
            min-width: 0;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .toolbar {{
            display: flex;
            gap: 10px;
            align-items: center;
            padding: 15px 20px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .toolbar-group {{
            display: flex;
            gap: 5px;
            align-items: center;
            padding: 0 10px;
            border-right: 1px solid #ddd;
        }}
        
        .toolbar-group:last-child {{
            border-right: none;
        }}
        
        .toolbar-label {{
            font-size: 0.9em;
            color: #666;
            margin-right: 5px;
        }}
        
        .toolbar-btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }}
        
        .toolbar-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }}
        
        .toolbar-btn.active {{
            background: #28a745;
        }}
        
        .toolbar-btn.danger {{
            background: #dc3545;
        }}
        
        .toolbar-btn.danger:hover {{
            background: #c82333;
        }}
        
        .time-range-display {{
            padding: 8px 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 5px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .annotation-panel {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 20px;
            z-index: 20000;
            display: none;
            min-width: 350px;
        }}
        
        .annotation-panel h3 {{
            margin-bottom: 15px;
            color: #667eea;
        }}
        
        .annotation-panel textarea {{
            width: 100%;
            height: 100px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
            resize: vertical;
        }}
        
        .annotation-panel .btn-group {{
            margin-top: 15px;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }}
        
        .annotation-panel button {{
            padding: 8px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .annotation-panel .btn-save {{
            background: #667eea;
            color: white;
        }}
        
        .annotation-panel .btn-cancel {{
            background: #6c757d;
            color: white;
        }}
        
        .annotation-panel .btn-delete {{
            background: #dc3545;
            color: white;
        }}
        
        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 19999;
            display: none;
        }}
        
        .selection-info {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            display: none;
        }}
        
        .selection-info .count {{
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        #chart-container {{
            width: 100%;
            height: calc(100vh - 180px);
            min-height: 600px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }}
        

    </style>
</head>
<body>
    <div class="main-layout">
        <div class="sidebar">
            <div class="sidebar-header">
                <h3>📂 Categories</h3>
                <p>Check to show/hide</p>
            </div>
            <div class="sidebar-actions">
                <button class="btn-select-all" id="select-all">✓ Select All</button>
                <button class="btn-select-none" id="select-none">✗ Select None</button>
            </div>
            <div class="sidebar-content" id="sidebar-content">
                <!-- Dynamic content -->
            </div>
        </div>
        
        <div class="container">
            <div class="header">
                <h1>{title}</h1>
                <p>Log Timeline Visualization - ECharts</p>
            </div>
            <div class="content">
                <div class="toolbar">
                    <div class="toolbar-group">
                        <span class="toolbar-label">⌚ Time Range:</span>
                        <span class="time-range-display" id="time-range-display">Loading...</span>
                    </div>
                    <div class="toolbar-group">
                        <span class="toolbar-label">📌 Annotations (double-click):</span>
                        <button class="toolbar-btn" id="toggle-annotations">👁 Show Annotations</button>
                        <button class="toolbar-btn" id="export-annotations">💾 Export</button>
                        <button class="toolbar-btn" id="import-annotations">📂 Import</button>
                    </div>
                    <div class="toolbar-group">
                        <span class="toolbar-label">✂️ Selection:</span>
                        <button class="toolbar-btn" id="lasso-select">⭕ Draw Selection</button>
                        <button class="toolbar-btn danger" id="clear-selection" style="display:none;">✖ Clear Selection</button>
                        <button class="toolbar-btn" id="reset-view">🔄 Reset View</button>
                        <button class="toolbar-btn" id="export-data">💾 Export Data</button>
                    </div>
                </div>
                
                <div id="chart-container"></div>
            </div>
        </div>
    </div>
    
    <!-- Annotation Panel -->
    <div class="overlay" id="overlay"></div>
    <div class="annotation-panel" id="annotation-panel">
        <h3>📝 Add Annotation</h3>
        <div id="annotation-point-info" style="margin-bottom: 10px; font-size: 12px; color: #666;"></div>
        <div style="margin-bottom: 10px;">
            <label style="font-size: 12px; color: #666; margin-right: 10px;">Label Color:</label>
            <input type="color" id="annotation-color" value="#667eea" style="width: 60px; height: 28px; border: none; cursor: pointer;">
            <span id="color-presets" style="margin-left: 10px;">
                <span class="color-preset" data-color="#667eea" style="display:inline-block;width:20px;height:20px;background:#667eea;border-radius:3px;cursor:pointer;margin-right:5px;vertical-align:middle;"></span>
                <span class="color-preset" data-color="#28a745" style="display:inline-block;width:20px;height:20px;background:#28a745;border-radius:3px;cursor:pointer;margin-right:5px;vertical-align:middle;"></span>
                <span class="color-preset" data-color="#dc3545" style="display:inline-block;width:20px;height:20px;background:#dc3545;border-radius:3px;cursor:pointer;margin-right:5px;vertical-align:middle;"></span>
                <span class="color-preset" data-color="#ffc107" style="display:inline-block;width:20px;height:20px;background:#ffc107;border-radius:3px;cursor:pointer;margin-right:5px;vertical-align:middle;"></span>
                <span class="color-preset" data-color="#17a2b8" style="display:inline-block;width:20px;height:20px;background:#17a2b8;border-radius:3px;cursor:pointer;vertical-align:middle;"></span>
            </span>
        </div>
        <textarea id="annotation-text" placeholder="Enter annotation content..."></textarea>
        <div class="btn-group">
            <button class="btn-delete" id="annotation-delete" style="display:none;">Delete</button>
            <button class="btn-cancel" id="annotation-cancel">Cancel</button>
            <button class="btn-save" id="annotation-save">Save</button>
        </div>
    </div>
    
    <!-- Selection Info -->
    <div class="selection-info" id="selection-info">
        <span>Selection contains: <span class="count" id="selection-count">0</span> points | Click "Clear Selection" to cancel</span>
    </div>
    
    <!-- Hidden file input -->
    <input type="file" id="import-file" accept=".json" style="display:none;">
    
    <script>
        // Initialize ECharts
        const chartDom = document.getElementById('chart-container');
        const myChart = echarts.init(chartDom);
        
        // Time formatting function
        function formatTime(ms) {{
            const date = new Date(ms);
            const h = String(date.getHours()).padStart(2, '0');
            const m = String(date.getMinutes()).padStart(2, '0');
            const s = String(date.getSeconds()).padStart(2, '0');
            const msStr = String(date.getMilliseconds()).padStart(3, '0');
            return h + ':' + m + ':' + s + '.' + msStr;
        }}
        
        // Duration formatting function (adaptive units)
        function formatDuration(ms) {{
            if (ms < 0) ms = Math.abs(ms);
            
            const units = [
                {{ name: 'd', value: 86400000 }},
                {{ name: 'h', value: 3600000 }},
                {{ name: 'm', value: 60000 }},
                {{ name: 's', value: 1000 }},
                {{ name: 'ms', value: 1 }}
            ];
            
            if (ms === 0) return '0ms';
            
            // Find largest non-zero unit
            let result = [];
            let remaining = ms;
            
            for (const unit of units) {{
                if (remaining >= unit.value) {{
                    const count = Math.floor(remaining / unit.value);
                    remaining = remaining % unit.value;
                    result.push(count + unit.name);
                    // Show max 2 units for brevity
                    if (result.length >= 2) break;
                }}
            }}
            
            return result.join('') || '0ms';
        }}
        
        // Prepare data
        const chartData = {chart_data_json};
        const classHierarchy = {class_hierarchy_json};
        
        // Primary category colors (for visual distinction)
        const classColors = [
            '#e3f2fd', '#f3e5f5', '#e8f5e9', '#fff3e0', '#fce4ec', 
            '#e0f7fa', '#f1f8e9', '#ede7f6', '#fff8e1', '#e1f5fe'
        ];
        
        // Precompute point counts by category (avoid repeated traversal)
        const pointCountByClass = {{}};
        const pointCountByCategory = {{}};
        chartData.rawData.forEach(p => {{
            pointCountByClass[p.classname] = (pointCountByClass[p.classname] || 0) + 1;
            pointCountByCategory[p.category] = (pointCountByCategory[p.category] || 0) + 1;
        }});
        
        // Currently displayed subclass set
        let visibleSubclasses = new Set();
        chartData.classHierarchy.forEach(cls => {{
            cls.subclasses.forEach(sub => {{
                visibleSubclasses.add(sub.category_label);
            }});
        }});
        
        // Generate sidebar content
        function generateSidebar() {{
            const container = document.getElementById('sidebar-content');
            let html = '';
            
            classHierarchy.forEach((cls, classIndex) => {{
                const bgColor = classColors[classIndex % classColors.length];
                const pointCount = pointCountByClass[cls.classname] || 0;
                
                html += `<div class="class-group">`;
                html += `<div class="class-header" style="background: ${{bgColor}};" data-class-index="${{classIndex}}">`;
                html += `<span class="toggle-icon">▼</span>`;
                html += `<span style="flex:1;">${{cls.classname}}</span>`;
                html += `<span class="point-count">${{pointCount}}</span>`;
                html += `</div>`;
                html += `<div class="subclass-list" data-class-index="${{classIndex}}">`;
                
                cls.subclasses.forEach((sub, subIndex) => {{
                    const subPointCount = pointCountByCategory[sub.category_label] || 0;
                    const checkId = `check_${{classIndex}}_${{subIndex}}`;
                    const isChecked = visibleSubclasses.has(sub.category_label) ? 'checked' : '';
                    
                    html += `<div class="subclass-item" style="border-left: 3px solid ${{classColors[classIndex % classColors.length]}}">`;
                    html += `<input type="checkbox" id="${{checkId}}" data-category="${{sub.category_label}}" ${{isChecked}}>`;
                    html += `<label for="${{checkId}}">${{sub.subclassname}}</label>`;
                    html += `<span class="point-count">${{subPointCount}}</span>`;
                    html += `</div>`;
                }});
                
                html += `</div></div>`;
            }});
            
            container.innerHTML = html;
            
            // Bind collapse events
            document.querySelectorAll('.class-header').forEach(header => {{
                header.addEventListener('click', function() {{
                    const index = this.dataset.classIndex;
                    const list = document.querySelector(`.subclass-list[data-class-index="${{index}}"]`);
                    list.classList.toggle('collapsed');
                    this.classList.toggle('collapsed');
                }});
            }});
            
            // Bind checkbox events
            document.querySelectorAll('.subclass-item input[type="checkbox"]').forEach(checkbox => {{
                checkbox.addEventListener('change', function() {{
                    const category = this.dataset.category;
                    if (this.checked) {{
                        visibleSubclasses.add(category);
                    }} else {{
                        visibleSubclasses.delete(category);
                    }}
                    updateChart();
                }});
            }});
        }}
        
        // Update chart
        function updateChart() {{
            // Recalculate Y-axis and series based on visibleSubclasses
            const filteredCategories = [];
            const categoryIndexMap = {{}};
            
            // Filter visible categories in original order
            chartData.yAxisData.forEach(cat => {{
                if (visibleSubclasses.has(cat)) {{
                    categoryIndexMap[cat] = filteredCategories.length;
                    filteredCategories.push(cat);
                }}
            }});
            
            // Rebuild series (merge filter and grouping for efficiency)
            // Layer color palette for cycling
            const layerColorPalette = [
                '#667eea', '#28a745', '#ffc107', '#dc3545', '#17a2b8',
                '#fd7e14', '#6f42c1', '#20c997', '#e83e8c', '#007bff',
                '#6610f2', '#795548', '#607d8b', '#4caf50', '#ff5722',
                '#9c27b0', '#00bcd4', '#8bc34a', '#ff9800', '#3f51b5'
            ];
            const getLayerColor = (layer) => layerColorPalette[(layer - 1) % layerColorPalette.length];
            const getLayerName = (layer) => 'Layer ' + layer;
            
            const subclassLayerSeries = {{}};
            const rawData = chartData.rawData;
            const rawLen = rawData.length;
            
            for (let i = 0; i < rawLen; i++) {{
                const point = rawData[i];
                if (!visibleSubclasses.has(point.category)) continue;
                
                const key = point.subclassname + '_' + point.layer;
                if (!subclassLayerSeries[key]) {{
                    subclassLayerSeries[key] = {{
                        subclassname: point.subclassname,
                        layer: point.layer,
                        data: []
                    }};
                }}
                
                // Recalculate Y-axis index
                subclassLayerSeries[key].data.push({{
                    value: [point.display_timestamp_ms, categoryIndexMap[point.category], point.cursor],
                    cursor: point.cursor,
                    msg: point.msg,
                    line: point.line,
                    layer: point.layer,
                    classname: point.classname,
                    subclassname: point.subclassname,
                    timeStr: point.timeStr
                }});
            }}
            
            const newSeries = [];
            Object.values(subclassLayerSeries).forEach(group => {{
                const layerColor = getLayerColor(group.layer);
                newSeries.push({{
                    name: group.subclassname + ' - ' + getLayerName(group.layer),
                    type: 'scatter',
                    data: group.data,
                    symbolSize: 12,
                    itemStyle: {{
                        color: layerColor,
                        borderColor: '#fff',
                        borderWidth: 2
                    }},
                    emphasis: {{
                        scale: 1.5,
                        itemStyle: {{
                            shadowBlur: 10,
                            shadowColor: layerColor
                        }}
                    }}
                }});
            }});
            
            // Calculate primary class area markers
            const markAreaData = [];
            let currentIndex = 0;
            const hierLen = classHierarchy.length;
            for (let clsIdx = 0; clsIdx < hierLen; clsIdx++) {{
                const cls = classHierarchy[clsIdx];
                let visibleCount = 0;
                const subs = cls.subclasses;
                const subsLen = subs.length;
                for (let j = 0; j < subsLen; j++) {{
                    if (visibleSubclasses.has(subs[j].category_label)) visibleCount++;
                }}
                if (visibleCount > 0) {{
                    // Use alternating opacity to distinguish adjacent class regions
                    const opacity = (clsIdx % 2 === 0) ? '20' : '40';
                    markAreaData.push([
                        {{
                            yAxis: currentIndex,
                            itemStyle: {{ color: classColors[clsIdx % classColors.length] + opacity }}
                        }},
                        {{ yAxis: currentIndex + visibleCount - 1 }}
                    ]);
                    currentIndex += visibleCount;
                }}
            }}
            
            // Add transparent series for area markers
            if (markAreaData.length > 0) {{
                newSeries.unshift({{
                    name: '_markArea',
                    type: 'scatter',
                    data: [],
                    markArea: {{
                        silent: true,
                        data: markAreaData
                    }}
                }});
            }}
            
            // Update chart height based on category count
            const chartHeight = Math.max(400, filteredCategories.length * 60 + 200);
            document.getElementById('chart-container').style.height = chartHeight + 'px';
            myChart.resize();
            
            // Apply new configuration
            myChart.setOption({{
                yAxis: {{
                    data: filteredCategories
                }},
                series: newSeries
            }}, {{
                replaceMerge: ['series']
            }});
            
            // Clear connection lines
            clearConnectionLines();
            
            // Re-render annotations considering visibility changes
            setTimeout(renderAnnotations, 100);
        }}
        
        // Select all button
        document.getElementById('select-all').addEventListener('click', function() {{
            document.querySelectorAll('.subclass-item input[type="checkbox"]').forEach(cb => {{
                cb.checked = true;
                visibleSubclasses.add(cb.dataset.category);
            }});
            updateChart();
        }});
        
        document.getElementById('select-none').addEventListener('click', function() {{
            document.querySelectorAll('.subclass-item input[type="checkbox"]').forEach(cb => {{
                cb.checked = false;
            }});
            visibleSubclasses.clear();
            updateChart();
        }});
        
        // Initialize sidebar
        generateSidebar();
        
        // Configuration options
        const option = {{
            title: {{
                text: 'Log Timeline Analysis',
                left: 'center',
                top: 10,
                textStyle: {{
                    fontSize: 20,
                    color: '#667eea'
                }}
            }},
            tooltip: {{
                trigger: 'item',
                confine: false,
                enterable: true,
                hideDelay: 500,
                appendToBody: true,
                position: function(point, params, dom, rect, size) {{
                    // Get viewport dimensions
                    const viewWidth = window.innerWidth;
                    const viewHeight = window.innerHeight;
                    const tooltipWidth = size.contentSize[0];
                    const tooltipHeight = size.contentSize[1];
                    
                    // Default position: very close to mouse cursor
                    let x = point[0] + 5;
                    let y = point[1] + 5;
                    
                    // Right boundary check: if exceeds right, show on left side of mouse
                    if (x + tooltipWidth > viewWidth - 10) {{
                        x = point[0] - tooltipWidth - 5;
                    }}
                    
                    // Bottom boundary check: if exceeds bottom, show above mouse
                    if (y + tooltipHeight > viewHeight - 10) {{
                        y = point[1] - tooltipHeight - 5;
                    }}
                    
                    // Ensure not exceeding left and top boundaries
                    x = Math.max(10, x);
                    y = Math.max(10, y);
                    
                    return [x, y];
                }},
                axisPointer: {{
                    type: 'none'
                }},
                formatter: function(params) {{
                    if (!params || !params.data) return '';
                    const data = params.data;
                    
                    // Detect nearby dense points (based on pixel distance, changes with zoom)
                    const currentSubclass = data.subclassname;
                    const currentClassname = data.classname;
                    const currentX = params.data.value[0];
                    const currentY = params.data.value[1];
                    
                    // Get current point pixel position
                    const currentPixel = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [currentX, currentY]);
                    const pixelThreshold = 40; // Points within 40 pixels are considered dense
                    
                    // Use index to get points of same category, avoid traversing all points
                    const categoryKey = currentClassname + '|' + currentSubclass;
                    const categoryPoints = pointsByCategory[categoryKey] || [];
                    
                    // Collect points with close pixel distance
                    let nearbyPoints = [];
                    
                    for (let i = 0; i < categoryPoints.length; i++) {{
                        const point = categoryPoints[i];
                        // Calculate pixel distance
                        const pointPixel = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [point.x, point.y]);
                        if (pointPixel && currentPixel) {{
                            const pixelDistance = Math.abs(pointPixel[0] - currentPixel[0]);
                            if (pixelDistance <= pixelThreshold) {{
                                nearbyPoints.push(point);
                            }}
                        }}
                    }}
                    
                    // Sort by time and line number
                    nearbyPoints.sort((a, b) => {{
                        if (a.x !== b.x) return a.x - b.x;
                        return a.line - b.line;
                    }});
                    
                    // If only 1 point, show single point details
                    if (nearbyPoints.length <= 1) {{
                        let html = '<div style="padding: 8px; max-width: 400px;">';
                        html += '<strong style="color: ' + params.color + '; font-size: 13px;">📌 ' + data.cursor + '</strong>';
                        html += '<span style="font-size: 11px; color: #666; margin-left: 8px;">Line ' + data.line + ' | Layer ' + data.layer + '</span>';
                        html += '<div style="margin-top: 6px; padding: 6px; background: #f8f9fa; border-radius: 4px; font-size: 11px; word-wrap: break-word; white-space: pre-wrap;">';
                        html += data.msg;
                        html += '</div>';
                        html += '</div>';
                        return html;
                    }}
                    
                    // Multiple points, show list
                    // Layer color palette for cycling
                    const layerColorPalette = [
                        '#667eea', '#28a745', '#ffc107', '#dc3545', '#17a2b8',
                        '#fd7e14', '#6f42c1', '#20c997', '#e83e8c', '#007bff',
                        '#6610f2', '#795548', '#607d8b', '#4caf50', '#ff5722',
                        '#9c27b0', '#00bcd4', '#8bc34a', '#ff9800', '#3f51b5'
                    ];
                    const getLayerColor = (layer) => layerColorPalette[(layer - 1) % layerColorPalette.length];
                    let html = '<div id="tooltip-scroll-container" style="padding: 10px; max-width: 500px; max-height: 60vh; overflow-y: auto;">';
                    html += '<div style="font-weight: bold; font-size: 14px; margin-bottom: 10px; color: #667eea;">🔍 Dense Area (' + nearbyPoints.length + ' points)</div>';
                    
                    nearbyPoints.forEach((point, index) => {{
                        const borderColor = getLayerColor(point.layer);
                        const isCurrentPoint = (point.x === currentX && point.line === data.line);
                        const bgColor = isCurrentPoint ? '#e7f1ff' : '#f8f9fa';
                        
                        html += '<div style="padding: 8px; margin: 6px 0; background: ' + bgColor + '; border-radius: 6px; border-left: 4px solid ' + borderColor + ';">';
                        html += '<div style="font-weight: bold; font-size: 12px; color: #333;">';
                        html += (isCurrentPoint ? '👉 ' : '') + '#' + (index + 1) + ' ' + point.cursor + '</div>';
                        html += '<div style="font-size: 11px; color: #666; margin: 3px 0;">⏰ ' + point.timeStr + ' | Line: ' + point.line + ' | Layer ' + point.layer + '</div>';
                        html += '<div style="font-size: 11px; color: #888; word-wrap: break-word; white-space: pre-wrap;">💬 ' + point.msg + '</div>';
                        html += '</div>';
                    }});
                    
                    html += '</div>';
                    return html;
                }},
                backgroundColor: 'rgba(255, 255, 255, 0.98)',
                borderColor: '#667eea',
                borderWidth: 2,
                textStyle: {{
                    color: '#333'
                }},
                extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.15); pointer-events: auto;'
            }},
            grid: {{
                left: '220px',
                right: '50px',
                top: '80px',
                bottom: '120px',
                containLabel: false
            }},
            xAxis: {{
                type: 'time',
                axisPointer: {{
                    show: true,
                    type: 'line',
                    lineStyle: {{
                        color: '#667eea',
                        width: 1,
                        type: 'solid'
                    }},
                    label: {{
                        show: true,
                        backgroundColor: '#667eea',
                        formatter: function(params) {{
                            const date = new Date(params.value);
                            const h = String(date.getHours()).padStart(2, '0');
                            const m = String(date.getMinutes()).padStart(2, '0');
                            const s = String(date.getSeconds()).padStart(2, '0');
                            const ms = String(date.getMilliseconds()).padStart(3, '0');
                            return h + ':' + m + ':' + s + '.' + ms;
                        }}
                    }}
                }},
                axisLabel: {{
                    formatter: function(value) {{
                        const date = new Date(value);
                        const h = String(date.getHours()).padStart(2, '0');
                        const m = String(date.getMinutes()).padStart(2, '0');
                        const s = String(date.getSeconds()).padStart(2, '0');
                        const ms = String(date.getMilliseconds()).padStart(3, '0');
                        return h + ':' + m + ':' + s + '.' + ms;
                    }},
                    rotate: 45
                }},
                splitLine: {{
                    show: true,
                    lineStyle: {{
                        type: 'dashed',
                        color: '#e0e0e0'
                    }}
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#999'
                    }}
                }}
            }},
            yAxis: {{
                type: 'category',
                data: chartData.yAxisData,
                axisPointer: {{
                    show: false,
                    type: 'none'
                }},
                axisLabel: {{
                    fontSize: 11,
                    width: 200,
                    overflow: 'break',
                    formatter: function(value) {{
                        // Extract subclassname after '|' separator
                        const idx = value.indexOf('|');
                        return idx >= 0 ? value.substring(idx + 1) : value;
                    }}
                }},
                splitLine: {{
                    show: true,
                    lineStyle: {{
                        type: 'dashed',
                        color: '#f0f0f0'
                    }}
                }},
                axisLine: {{
                    lineStyle: {{
                        color: '#999'
                    }}
                }}
            }},
            dataZoom: [
                {{
                    id: 'dataZoomX',
                    type: 'slider',
                    xAxisIndex: 0,
                    start: 0,
                    end: 100,
                    height: 30,
                    bottom: 70,
                    brushSelect: false,
                    handleSize: '80%',
                    dataBackground: {{
                        lineStyle: {{
                            color: '#667eea'
                        }},
                        areaStyle: {{
                            color: 'rgba(102, 126, 234, 0.2)'
                        }}
                    }},
                    fillerColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: '#667eea',
                    handleStyle: {{
                        color: '#667eea'
                    }},
                    moveHandleStyle: {{
                        color: '#764ba2'
                    }},
                    textStyle: {{
                        color: '#666'
                    }}
                }},
                {{
                    id: 'dataZoomY',
                    type: 'inside',
                    xAxisIndex: 0,
                    start: 0,
                    end: 100,
                    zoomOnMouseWheel: true,
                    moveOnMouseMove: true,
                    moveOnMouseWheel: false
                }},
                {{
                    id: 'dataZoomYSlider',
                    type: 'slider',
                    yAxisIndex: 0,
                    start: 0,
                    end: 100,
                    right: 10,
                    width: 20,
                    brushSelect: false,
                    handleSize: '80%',
                    fillerColor: 'rgba(118, 75, 162, 0.2)',
                    borderColor: '#764ba2',
                    handleStyle: {{
                        color: '#764ba2'
                    }},
                    textStyle: {{
                        color: '#666'
                    }}
                }},
                {{
                    id: 'dataZoomYInside',
                    type: 'inside',
                    yAxisIndex: 0,
                    start: 0,
                    end: 100,
                    zoomOnMouseWheel: false,
                    moveOnMouseMove: false
                }}
            ],
            toolbox: {{
                feature: {{
                    dataZoom: {{
                        yAxisIndex: 'none',
                        title: {{
                            zoom: 'Area Zoom',
                            back: 'Restore'
                        }}
                    }},
                    restore: {{
                        title: 'Reset'
                    }},
                    saveAsImage: {{
                        title: 'Save Image',
                        name: 'timeline-{timestamp_str}',
                        pixelRatio: 2
                    }}
                }},
                right: 20,
                top: 20
            }},
            series: (function() {{
                // Calculate initial primary class area markers
                const markAreaData = [];
                let currentIndex = 0;
                classHierarchy.forEach((cls, clsIdx) => {{
                    const subsCount = cls.subclasses.length;
                    if (subsCount > 0) {{
                        // Use alternating opacity to distinguish adjacent class regions
                        const opacity = (clsIdx % 2 === 0) ? '20' : '40';
                        markAreaData.push([
                            {{
                                yAxis: currentIndex,
                                itemStyle: {{ color: classColors[clsIdx % classColors.length] + opacity }}
                            }},
                            {{ yAxis: currentIndex + subsCount - 1 }}
                        ]);
                        currentIndex += subsCount;
                    }}
                }});
                
                const allSeries = [...chartData.series];
                if (markAreaData.length > 0) {{
                    allSeries.unshift({{
                        name: '_markArea',
                        type: 'scatter',
                        data: [],
                        markArea: {{
                            silent: true,
                            data: markAreaData
                        }}
                    }});
                }}
                return allSeries;
            }})()
        }};
        
        myChart.setOption(option);
        
        // Set correct chart height during initialization
        const initialChartHeight = Math.max(400, chartData.yAxisData.length * 60 + 200);
        document.getElementById('chart-container').style.height = initialChartHeight + 'px';
        myChart.resize();
        
        // Layer connection feature - create overlay for drawing connection lines
        const chartContainer = document.getElementById('chart-container');
        const svgOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svgOverlay.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 50;';
        svgOverlay.id = 'connection-lines-svg';
        chartContainer.style.position = 'relative';
        chartContainer.appendChild(svgOverlay);
        
        // Layer color palette for cycling
        const layerColorPalette = [
            '#667eea', '#28a745', '#ffc107', '#dc3545', '#17a2b8',
            '#fd7e14', '#6f42c1', '#20c997', '#e83e8c', '#007bff',
            '#6610f2', '#795548', '#607d8b', '#4caf50', '#ff5722',
            '#9c27b0', '#00bcd4', '#8bc34a', '#ff9800', '#3f51b5'
        ];
        const getLayerColor = (layer) => layerColorPalette[(layer - 1) % layerColorPalette.length];
        
        // Clear connection lines
        function clearConnectionLines() {{
            svgOverlay.innerHTML = '';
        }}
        
        // Draw connection lines
        function drawConnectionLines(points, color) {{
            if (points.length < 2) return;
            
            // Sort by time
            points.sort((a, b) => a.x - b.x);
            
            // Clear old lines
            clearConnectionLines();
            
            // Draw connection lines
            for (let i = 0; i < points.length - 1; i++) {{
                const p1 = points[i];
                const p2 = points[i + 1];
                
                // Use category name for coordinate conversion
                const yCategory1 = chartData.yAxisData[p1.y];
                const yCategory2 = chartData.yAxisData[p2.y];
                
                // Convert to pixel coordinates
                const pixel1 = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [p1.x, yCategory1]);
                const pixel2 = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [p2.x, yCategory2]);
                
                if (pixel1 && pixel2 && !isNaN(pixel1[0]) && !isNaN(pixel1[1]) && 
                    !isNaN(pixel2[0]) && !isNaN(pixel2[1])) {{
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', pixel1[0]);
                    line.setAttribute('y1', pixel1[1]);
                    line.setAttribute('x2', pixel2[0]);
                    line.setAttribute('y2', pixel2[1]);
                    line.setAttribute('stroke', color);
                    line.setAttribute('stroke-width', '3');
                    line.setAttribute('stroke-dasharray', '8,4');
                    line.setAttribute('stroke-linecap', 'round');
                    svgOverlay.appendChild(line);
                }}
            }}
        }}
        
        // Draw connection lines on hover for points in same layer
        myChart.on('mouseover', function(params) {{
            if (params.componentType === 'series' && params.data) {{
                const hoveredLayer = params.data.layer;
                const hoveredClassname = params.data.classname;
                const hoveredSubclass = params.data.subclassname;
                
                // Use index to quickly get points of same category+layer
                const layerKey = hoveredClassname + '|' + hoveredSubclass + '|' + hoveredLayer;
                const layerPoints = pointsByCategoryLayer[layerKey] || [];
                
                // If multiple points, draw connection lines
                if (layerPoints.length > 1) {{
                    const sameLayerPoints = layerPoints.map(p => ({{ x: p.x, y: p.y }}));
                    drawConnectionLines(sameLayerPoints, getLayerColor(hoveredLayer));
                }}
            }}
        }});
        
        // Remove connection lines on mouse out
        myChart.on('mouseout', function(params) {{
            if (params.componentType === 'series') {{
                clearConnectionLines();
            }}
        }});
        
        // Clear connection lines on zoom
        myChart.on('dataZoom', function() {{
            clearConnectionLines();
        }});
        
        // Clear connection lines on window resize
        window.addEventListener('resize', function() {{
            clearConnectionLines();
        }});
        
        // Responsive design
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
        
        // Export data feature
        document.getElementById('export-data').addEventListener('click', function() {{
            const dataStr = JSON.stringify(chartData.rawData, null, 2);
            const blob = new Blob([dataStr], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'timeline-data-{timestamp_str}.json';
            a.click();
            URL.revokeObjectURL(url);
        }});
        
        // Reset view
        document.getElementById('reset-view').addEventListener('click', function() {{
            myChart.dispatchAction({{
                type: 'dataZoom',
                start: 0,
                end: 100
            }});
        }});
        
        // Dense points data for tooltip - build index for performance optimization
        const allPointsFlat = [];
        // Build index by classname+subclassname to avoid traversing all points each time
        const pointsByCategory = {{}};
        // Build index by classname+subclassname+layer for connection lines feature
        const pointsByCategoryLayer = {{}};
        
        chartData.series.forEach(series => {{
            const seriesData = series.data;
            const len = seriesData.length;
            for (let i = 0; i < len; i++) {{
                const point = seriesData[i];
                const flatPoint = {{
                    ...point,
                    x: point.value[0],
                    y: point.value[1]
                }};
                allPointsFlat.push(flatPoint);
                
                // Category index
                const categoryKey = point.classname + '|' + point.subclassname;
                (pointsByCategory[categoryKey] || (pointsByCategory[categoryKey] = [])).push(flatPoint);
                
                // Category+layer index
                const layerKey = categoryKey + '|' + point.layer;
                (pointsByCategoryLayer[layerKey] || (pointsByCategoryLayer[layerKey] = [])).push(flatPoint);
            }}
        }});
        
        // Hide tooltip when mouse leaves chart
        chartDom.addEventListener('mouseleave', function() {{
            myChart.dispatchAction({{
                type: 'hideTip'
            }});
        }});
        
        // Tooltip wheel event interception - use document-level capture phase listener
        document.addEventListener('wheel', function(e) {{
            const scrollContainer = document.getElementById('tooltip-scroll-container');
            if (scrollContainer) {{
                const rect = scrollContainer.getBoundingClientRect();
                const mouseX = e.clientX;
                const mouseY = e.clientY;
                // Check if mouse is within scroll container area
                if (mouseX >= rect.left && mouseX <= rect.right && 
                    mouseY >= rect.top && mouseY <= rect.bottom) {{
                    // Stop event propagation to ECharts
                    e.stopImmediatePropagation();
                    e.preventDefault();
                    // Manually scroll container
                    scrollContainer.scrollTop += e.deltaY;
                }}
            }}
        }}, {{ passive: false, capture: true }});
        
        // Listen for globalout event, hide tooltip when mouse leaves chart
        myChart.on('globalout', function() {{
            myChart.dispatchAction({{
                type: 'hideTip'
            }});
        }});
        
        // ========== Time Range Display Feature ==========
        const timeRangeDisplay = document.getElementById('time-range-display');
        
        function updateTimeRangeDisplay() {{
            try {{
                const option = myChart.getOption();
                const dataZoomOption = option.dataZoom[0];
                
                // Get current view time range
                const minTime = chartData.minTime;
                const maxTime = chartData.maxTime;
                const timeRange = maxTime - minTime;
                
                // Use percentage to calculate actual time
                const startPercent = dataZoomOption.start / 100;
                const endPercent = dataZoomOption.end / 100;
                
                const viewStart = minTime + timeRange * startPercent;
                const viewEnd = minTime + timeRange * endPercent;
                
                const duration = viewEnd - viewStart;
                timeRangeDisplay.textContent = formatTime(viewStart) + ' ~ ' + formatTime(viewEnd) + ' (Duration: ' + formatDuration(duration) + ')';
            }} catch (e) {{
                console.warn('Failed to update time range display:', e);
            }}
        }}
        
        // Initial update
        setTimeout(updateTimeRangeDisplay, 100);
        
        // Update on dataZoom change
        myChart.on('dataZoom', function() {{
            updateTimeRangeDisplay();
        }});
        
        // ========== Annotation Feature ==========
        const annotationStorageKey = 'timeline-annotations-{file_name}';
        let annotations = {{}};
        let showAnnotations = true;
        let currentAnnotationPoint = null;
        
        // Load annotations from localStorage
        function loadAnnotations() {{
            try {{
                const stored = localStorage.getItem(annotationStorageKey);
                if (stored) {{
                    annotations = JSON.parse(stored);
                }}
            }} catch (e) {{
                console.warn('Failed to load annotations:', e);
                annotations = {{}};
            }}
        }}
        
        // Save annotations to localStorage
        function saveAnnotations() {{
            try {{
                localStorage.setItem(annotationStorageKey, JSON.stringify(annotations));
            }} catch (e) {{
                console.warn('Failed to save annotations:', e);
            }}
        }}
        
        // Generate annotation key
        function getAnnotationKey(point) {{
            return point.classname + '|' + point.subclassname + '|' + point.value[0] + '|' + point.layer;
        }}
        
        // Show annotations on chart
        function renderAnnotations() {{
            if (!showAnnotations || Object.keys(annotations).length === 0) {{
                // Hide all annotations - use $action to ensure complete clear
                myChart.setOption({{
                    graphic: {{
                        elements: []
                    }}
                }}, {{replaceMerge: ['graphic']}});
                return;
            }}
            
            const elements = [];
            Object.keys(annotations).forEach((key, index) => {{
                const ann = annotations[key];
                
                // Check if annotation category is visible
                if (!visibleSubclasses.has(ann.yCategory)) {{
                    return; // Skip annotations for hidden categories
                }}
                
                const pixel = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [ann.x, ann.yCategory]);
                
                if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {{
                    const text = ann.text.length > 15 ? ann.text.substring(0, 15) + '…' : ann.text;
                    const color = ann.color || '#667eea';
                    const textWidth = Math.max(text.length * 7 + 16, 40);
                    
                    // Label background (directly above point)
                    elements.push({{
                        type: 'rect',
                        shape: {{
                            x: pixel[0] - textWidth / 2,
                            y: pixel[1] - 28,
                            width: textWidth,
                            height: 20,
                            r: 3
                        }},
                        style: {{
                            fill: color,
                            shadowBlur: 3,
                            shadowOffsetY: 1,
                            shadowColor: 'rgba(0,0,0,0.15)'
                        }},
                        z: 100,
                        silent: false,
                        onclick: function() {{
                            openAnnotationPanel(ann.pointData, true);
                        }}
                    }});
                    
                    // Label text
                    elements.push({{
                        type: 'text',
                        style: {{
                            text: text,
                            x: pixel[0],
                            y: pixel[1] - 18,
                            textAlign: 'center',
                            textVerticalAlign: 'middle',
                            fill: '#fff',
                            fontSize: 11
                        }},
                        z: 101,
                        silent: true
                    }});
                }}
            }});
            
            myChart.setOption({{
                graphic: {{
                    elements: elements
                }}
            }}, {{replaceMerge: ['graphic']}});
        }}
        
        // Open annotation panel
        function openAnnotationPanel(point, isEdit) {{
            currentAnnotationPoint = point;
            const key = getAnnotationKey(point);
            const existingAnnotation = annotations[key];
            
            document.getElementById('annotation-point-info').innerHTML = 
                '<strong>' + point.classname + '</strong> / ' + point.subclassname + '<br>' +
                '<span style="color:#667eea">' + formatTime(point.value[0]) + '</span> - Layer ' + point.layer;
            
            document.getElementById('annotation-text').value = existingAnnotation ? existingAnnotation.text : '';
            document.getElementById('annotation-color').value = existingAnnotation ? (existingAnnotation.color || '#667eea') : '#667eea';
            document.getElementById('annotation-delete').style.display = existingAnnotation ? 'inline-block' : 'none';
            
            document.getElementById('overlay').style.display = 'block';
            document.getElementById('annotation-panel').style.display = 'block';
            document.getElementById('annotation-text').focus();
        }}
        
        // Close annotation panel
        function closeAnnotationPanel() {{
            document.getElementById('overlay').style.display = 'none';
            document.getElementById('annotation-panel').style.display = 'none';
            currentAnnotationPoint = null;
        }}
        
        // Save current annotation
        document.getElementById('annotation-save').addEventListener('click', function() {{
            if (!currentAnnotationPoint) return;
            
            const text = document.getElementById('annotation-text').value.trim();
            const color = document.getElementById('annotation-color').value;
            const key = getAnnotationKey(currentAnnotationPoint);
            
            if (text) {{
                annotations[key] = {{
                    text: text,
                    color: color,
                    x: currentAnnotationPoint.value[0],
                    yCategory: chartData.yAxisData[currentAnnotationPoint.value[1]],
                    pointData: currentAnnotationPoint,
                    createdAt: new Date().toISOString()
                }};
            }} else {{
                delete annotations[key];
            }}
            
            saveAnnotations();
            renderAnnotations();
            closeAnnotationPanel();
        }});
        
        // Cancel annotation
        document.getElementById('annotation-cancel').addEventListener('click', closeAnnotationPanel);
        document.getElementById('overlay').addEventListener('click', closeAnnotationPanel);
        
        // Delete annotation
        document.getElementById('annotation-delete').addEventListener('click', function() {{
            if (!currentAnnotationPoint) return;
            const key = getAnnotationKey(currentAnnotationPoint);
            delete annotations[key];
            saveAnnotations();
            closeAnnotationPanel();
            // Re-render (using replaceMerge will auto-clear old ones)
            renderAnnotations();
        }});
        
        // toggleannotationdisplay
        document.getElementById('toggle-annotations').addEventListener('click', function() {{
            showAnnotations = !showAnnotations;
            this.textContent = showAnnotations ? '👁 Show Annotations' : '👁 Hide Annotations';
            this.classList.toggle('active', showAnnotations);
            renderAnnotations();
        }});
        
        // Export annotations
        document.getElementById('export-annotations').addEventListener('click', function() {{
            const exportData = {{
                fileName: '{file_name}',
                exportTime: new Date().toISOString(),
                annotations: annotations
            }};
            const dataStr = JSON.stringify(exportData, null, 2);
            const blob = new Blob([dataStr], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'annotations-{file_name}-' + new Date().toISOString().slice(0,10) + '.json';
            a.click();
            URL.revokeObjectURL(url);
        }});
        
        // Import annotations
        document.getElementById('import-annotations').addEventListener('click', function() {{
            document.getElementById('import-file').click();
        }});
        
        document.getElementById('import-file').addEventListener('change', function(e) {{
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(event) {{
                try {{
                    const imported = JSON.parse(event.target.result);
                    if (imported.annotations) {{
                        // Merge imported annotations
                        Object.assign(annotations, imported.annotations);
                        saveAnnotations();
                        renderAnnotations();
                        alert('✅ Successfully imported ' + Object.keys(imported.annotations).length + ' annotations');
                    }}
                }} catch (err) {{
                    alert('❌ Import failed: ' + err.message);
                }}
            }};
            reader.readAsText(file);
            e.target.value = ''; // Clear to allow reselection
        }});
        
        // Double-click to add annotation
        myChart.on('dblclick', function(params) {{
            if (params.componentType === 'series' && params.data) {{
                openAnnotationPanel(params.data, false);
            }}
        }});
        
        // Color preset click event
        document.querySelectorAll('.color-preset').forEach(el => {{
            el.addEventListener('click', function() {{
                document.getElementById('annotation-color').value = this.dataset.color;
            }});
        }});
        
        // Re-render annotation position after dataZoom (triggered for both X and Y axis)
        myChart.on('dataZoom', function() {{
            if (showAnnotations) {{
                setTimeout(renderAnnotations, 50);
            }}
        }});
        
        // Re-render annotations after window resize
        window.addEventListener('resize', function() {{
            if (showAnnotations) {{
                setTimeout(renderAnnotations, 100);
            }}
        }});
        
        // Load and render annotations
        loadAnnotations();
        setTimeout(renderAnnotations, 200);
        
        // ========== Lasso Selection Feature ==========
        let isLassoMode = false;
        let lassoPath = [];
        let selectedPoints = [];
        const lassoBtn = document.getElementById('lasso-select');
        const clearSelectionBtn = document.getElementById('clear-selection');
        const selectionInfo = document.getElementById('selection-info');
        const selectionCountSpan = document.getElementById('selection-count');
        
        // Create lasso canvas
        const lassoCanvas = document.createElement('canvas');
        lassoCanvas.id = 'lasso-canvas';
        lassoCanvas.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 60;';
        chartContainer.appendChild(lassoCanvas);
        const lassoCtx = lassoCanvas.getContext('2d');
        
        function resizeLassoCanvas() {{
            const rect = chartContainer.getBoundingClientRect();
            lassoCanvas.width = rect.width;
            lassoCanvas.height = rect.height;
        }}
        resizeLassoCanvas();
        window.addEventListener('resize', resizeLassoCanvas);
        myChart.on('dataZoom', resizeLassoCanvas);
        
        // Toggle lasso mode
        lassoBtn.addEventListener('click', function() {{
            isLassoMode = !isLassoMode;
            this.classList.toggle('active', isLassoMode);
            chartDom.style.cursor = isLassoMode ? 'crosshair' : 'default';
            
            // When enabling lasso mode, allow canvas to receive mouse events
            lassoCanvas.style.pointerEvents = isLassoMode ? 'auto' : 'none';
            
            if (isLassoMode) {{
                // Disable chart drag zoom
                myChart.setOption({{
                    dataZoom: [
                        {{ id: 'dataZoomX', zoomLock: true }},
                        {{ id: 'dataZoomY', zoomLock: true }}
                    ]
                }});
            }} else {{
                // Restore drag zoom
                myChart.setOption({{
                    dataZoom: [
                        {{ id: 'dataZoomX', zoomLock: false }},
                        {{ id: 'dataZoomY', zoomLock: false }}
                    ]
                }});
            }}
        }});
        
        // Check if point is inside polygon (using ray casting method)
        function isPointInPolygon(point, polygon) {{
            if (polygon.length < 3) return false;
            
            let inside = false;
            for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {{
                const xi = polygon[i][0], yi = polygon[i][1];
                const xj = polygon[j][0], yj = polygon[j][1];
                
                if (((yi > point[1]) !== (yj > point[1])) &&
                    (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi)) {{
                    inside = !inside;
                }}
            }}
            return inside;
        }}
        
        // Lasso drawing
        let isDrawing = false;
        
        // Use lassoCanvas instead of chartDom for event listening
        lassoCanvas.addEventListener('mousedown', function(e) {{
            if (!isLassoMode) return;
            
            const rect = lassoCanvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            isDrawing = true;
            lassoPath = [[x, y]];
            
            lassoCtx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
            lassoCtx.beginPath();
            lassoCtx.moveTo(x, y);
            lassoCtx.strokeStyle = '#667eea';
            lassoCtx.lineWidth = 2;
            lassoCtx.setLineDash([5, 5]);
        }});
        
        lassoCanvas.addEventListener('mousemove', function(e) {{
            if (!isLassoMode || !isDrawing) return;
            
            const rect = lassoCanvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            lassoPath.push([x, y]);
            
            // Redraw path
            lassoCtx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
            lassoCtx.beginPath();
            lassoCtx.moveTo(lassoPath[0][0], lassoPath[0][1]);
            for (let i = 1; i < lassoPath.length; i++) {{
                lassoCtx.lineTo(lassoPath[i][0], lassoPath[i][1]);
            }}
            lassoCtx.stroke();
            
            // Fill semi-transparent area
            lassoCtx.fillStyle = 'rgba(102, 126, 234, 0.1)';
            lassoCtx.fill();
        }});
        
        lassoCanvas.addEventListener('mouseup', function(e) {{
            if (!isLassoMode || !isDrawing) return;
            isDrawing = false;
            
            // Disable canvas events, restore chart interaction
            lassoCanvas.style.pointerEvents = 'none';
            
            if (lassoPath.length < 3) {{
                lassoCtx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
                return;
            }}
            
            // Close path
            lassoPath.push(lassoPath[0]);
            
            // Find selected points
            selectedPoints = [];
            allPointsFlat.forEach(point => {{
                const yCategory = chartData.yAxisData[point.y];
                const pixel = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [point.x, yCategory]);
                
                if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {{
                    if (isPointInPolygon(pixel, lassoPath)) {{
                        selectedPoints.push(point);
                    }}
                }}
            }});
            
            // Display selection results
            if (selectedPoints.length > 0) {{
                clearSelectionBtn.style.display = 'inline-block';
                selectionInfo.style.display = 'block';
                selectionCountSpan.textContent = selectedPoints.length;
                
                // Redraw closed selection area (keep selection box)
                redrawSelectionArea();
            }} else {{
                lassoCtx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
            }}
            
            // Exit lasso mode
            isLassoMode = false;
            lassoBtn.classList.remove('active');
            chartDom.style.cursor = 'default';
            myChart.setOption({{
                dataZoom: [
                    {{ id: 'dataZoomX', zoomLock: false }},
                    {{ id: 'dataZoomY', zoomLock: false }}
                ]
            }});
        }});
        
        // Redraw selection area (works correctly after zoom)
        function redrawSelectionArea() {{
            if (lassoPath.length < 3) return;
            
            lassoCtx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
            lassoCtx.beginPath();
            lassoCtx.moveTo(lassoPath[0][0], lassoPath[0][1]);
            for (let i = 1; i < lassoPath.length; i++) {{
                lassoCtx.lineTo(lassoPath[i][0], lassoPath[i][1]);
            }}
            lassoCtx.closePath();
            lassoCtx.strokeStyle = '#667eea';
            lassoCtx.lineWidth = 2;
            lassoCtx.setLineDash([5, 5]);
            lassoCtx.stroke();
            lassoCtx.fillStyle = 'rgba(102, 126, 234, 0.15)';
            lassoCtx.fill();
        }}
        
        // Get annotation graphics (no rendering, only return array)
        function renderAnnotationsGraphics() {{
            if (!showAnnotations) return [];
            
            const graphics = [];
            Object.keys(annotations).forEach((key, index) => {{
                const ann = annotations[key];
                
                // Check if annotation category is visible
                if (!visibleSubclasses.has(ann.yCategory)) {{
                    return; // Skip annotations for hidden categories
                }}
                
                const pixel = myChart.convertToPixel({{xAxisIndex: 0, yAxisIndex: 0}}, [ann.x, ann.yCategory]);
                
                if (pixel && !isNaN(pixel[0]) && !isNaN(pixel[1])) {{
                    const text = ann.text.length > 15 ? ann.text.substring(0, 15) + '…' : ann.text;
                    const color = ann.color || '#667eea';
                    const textWidth = Math.max(text.length * 7 + 16, 40);
                    
                    // Label background (directly above point)
                    graphics.push({{
                        type: 'rect',
                        shape: {{
                            x: pixel[0] - textWidth / 2,
                            y: pixel[1] - 28,
                            width: textWidth,
                            height: 20,
                            r: 3
                        }},
                        style: {{
                            fill: color,
                            shadowBlur: 3,
                            shadowOffsetY: 1,
                            shadowColor: 'rgba(0,0,0,0.15)'
                        }},
                        z: 100,
                        silent: false,
                        onclick: function() {{
                            openAnnotationPanel(ann.pointData, true);
                        }}
                    }});
                    
                    // Label text
                    graphics.push({{
                        type: 'text',
                        style: {{
                            text: text,
                            x: pixel[0],
                            y: pixel[1] - 18,
                            textAlign: 'center',
                            textVerticalAlign: 'middle',
                            fill: '#fff',
                            fontSize: 11
                        }},
                        z: 101,
                        silent: true
                    }});
                }}
            }});
            return graphics;
        }}
        
        // Clear selection
        clearSelectionBtn.addEventListener('click', function() {{
            selectedPoints = [];
            lassoPath = [];
            lassoCtx.clearRect(0, 0, lassoCanvas.width, lassoCanvas.height);
            this.style.display = 'none';
            selectionInfo.style.display = 'none';
            
            // Only keep annotation graphics
            renderAnnotations();
        }});
        
        // Note: Selection area is drawn on canvas, stays in place during zoom (expected behavior)
        // To clear selection, click the "Clear Selection" button
    </script>
</body>
</html>
"""
    
    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML file generated: {output_file}")
    print(f"📊 Summary: {total_classes} classes, {total_subclasses} subclasses, {total_points} points")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python json2html.py <input.json> [output.html]")
        print("Example: python json2html.py rules.json rules.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Default output filename
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        input_path = Path(input_file)
        output_file = input_path.with_suffix('.html')
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        # Read JSON file
        print(f"📖 Reading: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Generate HTML
        generate_html(data, output_file)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
