#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
log2json.py - Extract data from log files using ripgrep, generate JSON for json2html

Usage: python log2json.py <log_file> <config1.py> [config2.py ...] [-o output.json]

Examples:
    python log2json.py log/1.log configs/audio.py configs/system.py
    python log2json.py log/1.log configs/*.py -o result.json
"""

import json
import sys
import subprocess
import re
import os
import glob
import importlib.util
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Dict, Any, Callable, Union


# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_rg_path() -> str:
    """Get ripgrep executable path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_rg = os.path.join(script_dir, "rg", "rg.exe" if sys.platform == 'win32' else "rg")
    return local_rg if os.path.exists(local_rg) else "rg"


RG_PATH = get_rg_path()


def parse_logcat_timestamp(line: str, base_year: Optional[int] = None) -> int:
    """
    Parse Android logcat timestamp, return millisecond Unix timestamp.
    
    Supported formats:
    - "07-28 15:15:07.283" (standard logcat)
    - "01-01 08:00:00.096" (system boot time)
    
    Args:
        line: Log line
        base_year: Base year, defaults to current year
    
    Returns:
        Millisecond Unix timestamp, returns 0 on parse failure
    """
    if base_year is None:
        base_year = datetime.now().year
    
    match = re.match(r'^(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\.(\d{3})', line)
    if match:
        month, day, hour, minute, second, ms = match.groups()
        try:
            dt = datetime(base_year, int(month), int(day),
                         int(hour), int(minute), int(second))
            return int(dt.timestamp() * 1000) + int(ms)
        except ValueError:
            pass
    
    return 0


def run_rg_json(pattern: str, log_file: str) -> List[Dict[str, Any]]:
    """
    Run rg --json command and parse output.
    
    Args:
        pattern: Regex pattern
        log_file: Log file path
    
    Returns:
        List of match results with line_number, line_text, submatches
    """
    try:
        result = subprocess.run(
            [RG_PATH, "--json", "-e", pattern, log_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        matches = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get('type') == 'match':
                    match_data = data['data']
                    matches.append({
                        'line_number': match_data['line_number'],
                        'line_text': match_data['lines']['text'].strip(),
                        'submatches': match_data.get('submatches', [])
                    })
            except json.JSONDecodeError:
                continue
        
        return matches
    
    except FileNotFoundError:
        print("❌ Error: ripgrep not found, please ensure rg is in PATH or rg/ directory")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ Error running rg: {e}")
        return []


def extract_cursor(line: str, cursor_pattern: str, default: str = "MATCH") -> str:
    """
    Extract cursor (identifier) from log line.
    
    Args:
        line: Log line
        cursor_pattern: Regex pattern for cursor extraction
        default: Default value
    
    Returns:
        Extracted cursor or default value
    """
    if cursor_pattern:
        match = re.search(cursor_pattern, line)
        if match:
            cursor = match.group(0).strip()
            cursor = re.sub(r'[^\w\-_.]', '_', cursor)
            return cursor[:50]
    return default


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load Python configuration file.
    
    Config file should contain:
    - classname: str
    - subclasses: list
    - process_json (optional): function(result_json) -> result_json
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    path = Path(config_path)
    
    if not path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    if path.suffix != '.py':
        print(f"❌ Only .py config files are supported: {config_path}")
        sys.exit(1)
    
    try:
        spec = importlib.util.spec_from_file_location("config", config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return {
            'classname': getattr(module, 'classname', 'Unnamed'),
            'subclasses': getattr(module, 'subclasses', []),
            'process_json': getattr(module, 'process_json', None),
            '_module': module
        }
    except Exception as e:
        print(f"❌ Failed to load config {config_path}: {e}")
        sys.exit(1)


def resolve_callable(
    value: Union[str, int, Callable],
    line: str,
    match: Dict[str, Any],
    default: Union[str, int]
) -> Union[str, int]:
    """
    Resolve a value that may be a callable or static value.
    
    Args:
        value: Static value or callable (line, match) -> result
        line: Log line text
        match: Match info dictionary
        default: Default value on failure
    
    Returns:
        Resolved value
    """
    if callable(value):
        try:
            return value(line, match)
        except Exception:
            return default
    return value


def process_config(
    config: Dict[str, Any],
    log_file: str,
    base_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process a single config file, return class data.
    
    Supports:
    - subclassname: string or function (line, match) -> str
    - cursor: string or function (line, match) -> str
    - layer: integer or function (line, match) -> int
    
    Args:
        config: Configuration dictionary
        log_file: Log file path
        base_year: Base year for timestamp parsing
    
    Returns:
        Class data in json2html format
    """
    classname = config.get('classname', 'Unnamed')
    subclasses_config = config.get('subclasses', [])
    
    subclass_points_map: Dict[str, List[Dict]] = defaultdict(list)
    seen_lines: set = set()
    
    for sub_config in subclasses_config:
        subclassname_cfg = sub_config.get('subclassname', 'Unnamed')
        rules = sub_config.get('rules', [])
        
        for rule in rules:
            pattern = rule.get('pattern', '')
            if not pattern:
                continue
            
            cursor_cfg = rule.get('cursor')
            cursor_pattern = rule.get('cursor_pattern', '')
            cursor_prefix = rule.get('cursor_prefix', '')
            layer_cfg = rule.get('layer', 1)
            
            matches = run_rg_json(pattern, log_file)
            
            for match in matches:
                line_num = match['line_number']
                if line_num in seen_lines:
                    continue
                seen_lines.add(line_num)
                
                line_text = match['line_text']
                timestamp = parse_logcat_timestamp(line_text, base_year)
                
                # Resolve subclassname
                subclassname = resolve_callable(subclassname_cfg, line_text, match, 'Unnamed')
                
                # Resolve cursor
                if callable(cursor_cfg):
                    cursor = resolve_callable(cursor_cfg, line_text, match, f"L{line_num}")
                elif cursor_cfg:
                    cursor = cursor_cfg
                elif cursor_pattern:
                    extracted = extract_cursor(line_text, cursor_pattern, '')
                    cursor = cursor_prefix + extracted if extracted else f"L{line_num}"
                else:
                    cursor = f"L{line_num}"
                
                # Resolve layer
                layer = resolve_callable(layer_cfg, line_text, match, 1)
                
                subclass_points_map[subclassname].append({
                    'cursor': str(cursor),
                    'msg': line_text,
                    'line': line_num,
                    'timestamp': timestamp,
                    'layer': int(layer)
                })
    
    # Build result
    result = {
        'classname': classname,
        'subclasses': []
    }
    
    for subclassname, points in subclass_points_map.items():
        points.sort(key=lambda x: x['line'])
        if points:
            result['subclasses'].append({
                'subclassname': subclassname,
                'points': points
            })
    
    return result


def merge_results(
    configs_data: List[Dict],
    log_file: str,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Merge results from multiple configs.
    
    Args:
        configs_data: List of config data
        log_file: Log file path
        name: Output JSON name field
    
    Returns:
        Complete JSON data in json2html format
    """
    if name is None:
        name = f"Log Analysis - {Path(log_file).name}"
    
    return {
        'name': name,
        'all': configs_data
    }


def parse_args(argv: List[str]) -> tuple:
    """Parse command line arguments."""
    if len(argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    log_file = argv[1]
    config_files = []
    output_file = None
    name = None
    
    i = 2
    while i < len(argv):
        arg = argv[i]
        if arg == '-o' and i + 1 < len(argv):
            output_file = argv[i + 1]
            i += 2
        elif arg == '-n' and i + 1 < len(argv):
            name = argv[i + 1]
            i += 2
        else:
            config_files.append(arg)
            i += 1
    
    return log_file, config_files, output_file, name


def expand_config_patterns(patterns: List[str]) -> List[str]:
    """Expand glob patterns in config file list."""
    expanded = []
    for pattern in patterns:
        if '*' in pattern or '?' in pattern:
            matches = glob.glob(pattern)
            if matches:
                expanded.extend(sorted(matches))
            else:
                print(f"⚠️ No matching config files: {pattern}")
        else:
            expanded.append(pattern)
    return expanded


def main():
    """Main entry point."""
    log_file, config_files, output_file, name = parse_args(sys.argv)
    
    # Validate log file
    if not Path(log_file).exists():
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)
    
    # Validate config files
    if not config_files:
        print("❌ Please specify at least one config file")
        sys.exit(1)
    
    # Expand wildcards
    config_files = expand_config_patterns(config_files)
    if not config_files:
        print("❌ No config files found")
        sys.exit(1)
    
    # Default output filename
    if output_file is None:
        output_file = Path(log_file).stem + '_result.json'
    
    print(f"📖 Log file: {log_file}")
    print(f"📋 Config files: {', '.join(config_files)}")
    print(f"📝 Output file: {output_file}")
    print()
    
    # Process each config
    all_data = []
    total_points = 0
    process_json_callbacks = []

    for config_file in config_files:
        print(f"🔍 Processing: {config_file}")
        config = load_config(config_file)
        class_data = process_config(config, log_file)
        
        # Collect process_json callbacks
        if config.get('process_json'):
            process_json_callbacks.append((config_file, config['process_json']))
        
        class_points = sum(len(sub['points']) for sub in class_data['subclasses'])
        print(f"   ├─ Class: {class_data['classname']}")
        print(f"   ├─ Subclasses: {len(class_data['subclasses'])}")
        print(f"   └─ Points: {class_points}")
        
        if class_data['subclasses']:
            all_data.append(class_data)
            total_points += class_points
    
    print()
    
    # Merge and write results
    result = merge_results(all_data, log_file, name)
    
    # Call process_json callbacks from each config
    for config_file, process_fn in process_json_callbacks:
        try:
            print(f"🔧 Running process_json from: {config_file}")
            result = process_fn(result)
        except Exception as e:
            print(f"⚠️ process_json failed in {config_file}: {e}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    subclass_count = sum(len(c['subclasses']) for c in all_data)
    print(f"✅ Generated: {output_file}")
    print(f"📊 Summary: {len(all_data)} classes, {subclass_count} subclasses, {total_points} points")


if __name__ == "__main__":
    main()
