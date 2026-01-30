#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Log Self-Test Script

Test coverage:
1. log2json.py basic functionality
2. json2html.py basic functionality
3. Config file parsing (static/dynamic)
4. Complete workflow
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Set, Optional


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(msg: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {msg}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.RESET}")


def print_pass(msg: str) -> None:
    """Print pass message."""
    print(f"  {Colors.GREEN}✓ PASS:{Colors.RESET} {msg}")


def print_fail(msg: str) -> None:
    """Print fail message."""
    print(f"  {Colors.RED}✗ FAIL:{Colors.RESET} {msg}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"  {Colors.YELLOW}ℹ INFO:{Colors.RESET} {msg}")


class TestRunner:
    """Test runner for Quick Log project."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_dir = self.script_dir.parent
        self.test_log = self.script_dir / "test_log.log"
        self.test_config = self.script_dir / "test_config.py"
        self.passed = 0
        self.failed = 0
        self.temp_files: List[str] = []
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        for f in self.temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> tuple:
        """Run command and return result."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd or self.project_dir
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def test_log2json_basic(self) -> bool:
        """Test log2json.py basic functionality."""
        print_header("Testing log2json.py Basic Functionality")
        
        output_json = self.script_dir / "test_output.json"
        self.temp_files.append(str(output_json))
        
        cmd = [
            sys.executable,
            str(self.project_dir / "log2json.py"),
            str(self.test_log),
            str(self.test_config),
            "-o", str(output_json)
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode == 0:
            print_pass("log2json.py executed successfully")
            self.passed += 1
        else:
            print_fail(f"log2json.py execution failed: {stderr}")
            self.failed += 1
            return False
        
        if output_json.exists():
            print_pass("JSON output file generated")
            self.passed += 1
        else:
            print_fail("JSON output file not generated")
            self.failed += 1
            return False
        
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print_pass("JSON format is valid")
            self.passed += 1
        except json.JSONDecodeError as e:
            print_fail(f"Invalid JSON format: {e}")
            self.failed += 1
            return False
        
        if "all" in data and isinstance(data["all"], list):
            print_pass("JSON contains 'all' array")
            self.passed += 1
        else:
            print_fail("JSON missing 'all' array")
            self.failed += 1
        
        total_points = sum(
            len(sub.get("points", []))
            for cls in data.get("all", [])
            for sub in cls.get("subclasses", [])
        )
        
        if total_points > 0:
            print_pass(f"Matched {total_points} event points")
            self.passed += 1
        else:
            print_fail("No event points matched")
            self.failed += 1
        
        return True
    
    def test_json2html_basic(self) -> bool:
        """Test json2html.py basic functionality."""
        print_header("Testing json2html.py Basic Functionality")
        
        input_json = self.script_dir / "test_output.json"
        output_html = self.script_dir / "test_output.html"
        self.temp_files.append(str(output_html))
        
        if not input_json.exists():
            print_info("Skipped: requires log2json test to run first")
            return False
        
        cmd = [
            sys.executable,
            str(self.project_dir / "json2html.py"),
            str(input_json),
            str(output_html)
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode == 0:
            print_pass("json2html.py executed successfully")
            self.passed += 1
        else:
            print_fail(f"json2html.py execution failed: {stderr}")
            self.failed += 1
            return False
        
        if output_html.exists():
            print_pass("HTML output file generated")
            self.passed += 1
        else:
            print_fail("HTML output file not generated")
            self.failed += 1
            return False
        
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        if '<html' in html_content and 'echarts' in html_content.lower():
            print_pass("HTML contains ECharts content")
            self.passed += 1
        else:
            print_fail("HTML content incomplete")
            self.failed += 1
        
        return True
    
    def test_dynamic_functions(self) -> bool:
        """Test dynamic function features."""
        print_header("Testing Dynamic Function Features")
        
        input_json = self.script_dir / "test_output.json"
        
        if not input_json.exists():
            print_info("Skipped: requires log2json test to run first")
            return False
        
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cursors: Set[str] = set()
        subclassnames: Set[str] = set()
        layers: Set[int] = set()
        
        for cls in data.get("all", []):
            for sub in cls.get("subclasses", []):
                subclassnames.add(sub.get("subclassname", ""))
                for point in sub.get("points", []):
                    cursors.add(point.get("cursor", ""))
                    layers.add(point.get("layer", 0))
        
        # Test function-generated cursor (ITEM_1, ITEM_2)
        item_cursors = [c for c in cursors if c.startswith("ITEM_")]
        if item_cursors:
            print_pass(f"Function-generated cursor successful: {item_cursors}")
            self.passed += 1
        else:
            print_fail("Function-generated cursor not found (ITEM_*)")
            self.failed += 1
        
        # Test dynamic subclassname
        dynamic_names = [s for s in subclassnames if s in ["Error Events", "Warning Events", "General Events"]]
        if dynamic_names:
            print_pass(f"Dynamic subclassname successful: {dynamic_names}")
            self.passed += 1
        else:
            print_fail("Dynamic subclassname not found")
            self.failed += 1
        
        # Test layer values
        if layers and all(layer in [1, 2, 3] for layer in layers):
            print_pass(f"Layer values valid: {sorted(layers)}")
            self.passed += 1
        else:
            print_fail(f"Layer values invalid: {layers}")
            self.failed += 1
        
        return True
    
    def test_config_with_sample(self) -> bool:
        """Test with sample config files."""
        print_header("Testing Sample Config Files")
        
        sample_audio = self.project_dir / "configsSample" / "audio.py"
        sample_system = self.project_dir / "configsSample" / "system.py"
        
        if not sample_audio.exists():
            print_info("Skipped: configsSample/audio.py not found")
            return False
        
        output_json = self.script_dir / "sample_output.json"
        self.temp_files.append(str(output_json))
        
        log_file = self.project_dir / "log" / "1.log"
        if not log_file.exists():
            log_file = self.test_log
        
        cmd = [
            sys.executable,
            str(self.project_dir / "log2json.py"),
            str(log_file),
            str(sample_audio),
        ]
        
        if sample_system.exists():
            cmd.append(str(sample_system))
        
        cmd.extend(["-o", str(output_json)])
        
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode == 0:
            print_pass("Sample config executed successfully")
            self.passed += 1
        else:
            print_fail(f"Sample config execution failed: {stderr}")
            self.failed += 1
            return False
        
        if output_json.exists():
            with open(output_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            class_count = len(data.get("all", []))
            if class_count > 0:
                print_pass(f"Generated {class_count} primary class(es)")
                self.passed += 1
            else:
                print_info("No classes generated (log content may not match)")
        
        return True
    
    def test_timestamp_parsing(self) -> bool:
        """Test timestamp parsing."""
        print_header("Testing Timestamp Parsing")
        
        input_json = self.script_dir / "test_output.json"
        
        if not input_json.exists():
            print_info("Skipped: requires log2json test to run first")
            return False
        
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        timestamps = [
            point.get("timestamp", 0)
            for cls in data.get("all", [])
            for sub in cls.get("subclasses", [])
            for point in sub.get("points", [])
            if point.get("timestamp", 0) > 0
        ]
        
        if timestamps:
            if all(ts > 1000000000000 for ts in timestamps):
                print_pass(f"Timestamps are in millisecond format ({len(timestamps)} total)")
                self.passed += 1
            else:
                print_fail("Timestamp format incorrect")
                self.failed += 1
            
            sorted_ts = sorted(timestamps)
            if timestamps == sorted_ts or timestamps == sorted_ts[::-1]:
                print_pass("Timestamps are ordered correctly")
                self.passed += 1
            else:
                print_info("Timestamps not in order (may be normal)")
        else:
            print_fail("No valid timestamps parsed")
            self.failed += 1
        
        return True
    
    def run_all_tests(self) -> int:
        """Run all tests and return exit code."""
        print(f"\n{Colors.BOLD}Quick Log Automated Tests{Colors.RESET}")
        print(f"Project dir: {self.project_dir}")
        print(f"Test dir: {self.script_dir}")
        
        try:
            self.test_log2json_basic()
            self.test_json2html_basic()
            self.test_dynamic_functions()
            self.test_timestamp_parsing()
            self.test_config_with_sample()
        finally:
            pass  # Keep output files for inspection
        
        print_header("Test Results Summary")
        total = self.passed + self.failed
        print(f"  Total: {total} tests")
        print(f"  {Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {self.failed}{Colors.RESET}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.RESET}")
            return 1


def main():
    """Main entry point."""
    runner = TestRunner()
    sys.exit(runner.run_all_tests())


if __name__ == "__main__":
    main()
