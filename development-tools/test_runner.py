#!/usr/bin/env python3
"""
Quick Test Runner for Records Management Module

This script provides easy commands for running tests and fixing issues.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_comprehensive_test_generation():
    """Generate tests for all models"""
    script_path = Path(__file__).parent / "comprehensive_test_generator.py"
    cmd = ["python3", str(script_path)]

    print("🚀 Generating comprehensive tests...")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0

def run_specific_tests(test_pattern=""):
    """Run specific tests matching pattern"""
    base_path = Path(__file__).parent.parent

    cmd = [
        "python3", "-m", "pytest",
        str(base_path / "records_management" / "tests"),
        "-v", "--tb=short"
    ]

    if test_pattern:
        cmd.extend(["-k", test_pattern])

    print(f"🧪 Running tests{f' matching: {test_pattern}' if test_pattern else ''}...")
    result = subprocess.run(cmd, cwd=base_path)
    return result.returncode == 0

def run_odoo_tests():
    """Run tests using Odoo's test framework"""
    base_path = Path(__file__).parent.parent

    cmd = [
        "python3", "-m", "odoo",
        "--test-enable",
        "--stop-after-init",
        "--database=test_records_management",
        f"--addons-path={base_path}",
        "-i", "records_management",
        "--log-level=test"
    ]

    print("🧪 Running Odoo framework tests...")
    result = subprocess.run(cmd, cwd=base_path)
    return result.returncode == 0

def validate_test_structure():
    """Validate that tests are in correct directory structure"""
    base_path = Path(__file__).parent.parent
    tests_dir = base_path / "records_management" / "tests"
    models_dir = base_path / "records_management" / "models"

    print("🔍 Validating test structure...")

    # Check for test files in wrong location
    wrong_location_tests = list(models_dir.glob("test_*.py"))
    if wrong_location_tests:
        print("❌ Found test files in models directory:")
        for test_file in wrong_location_tests:
            print(f"  - {test_file}")
        print(f"  → Move these to: {tests_dir}")
        return False

    # Check tests directory structure
    if not tests_dir.exists():
        print(f"❌ Tests directory does not exist: {tests_dir}")
        return False

    if not (tests_dir / "__init__.py").exists():
        print(f"❌ Missing __init__.py in tests directory")
        return False

    test_files = list(tests_dir.glob("test_*.py"))
    print(f"✅ Found {len(test_files)} test files in correct location:")
    for test_file in test_files:
        print(f"  ✅ {test_file.name}")

    return True

def show_test_coverage():
    """Show current test coverage"""
    base_path = Path(__file__).parent.parent

    # Run the test generator in report mode
    script_path = Path(__file__).parent / "comprehensive_test_generator.py"
    cmd = ["python3", str(script_path)]

    result = subprocess.run(cmd, cwd=base_path, capture_output=True, text=True)
    print(result.stdout)

    return result.returncode == 0

def main():
    """Main command interface"""
    if len(sys.argv) < 2:
        print("""
🧪 Records Management Test Runner

Usage:
    python3 test_runner.py <command>

Commands:
    generate     - Generate tests for all models
    validate     - Validate test directory structure
    coverage     - Show test coverage report
    run          - Run all tests
    run <pattern> - Run tests matching pattern
    odoo         - Run tests with Odoo framework

Examples:
    python3 test_runner.py generate
    python3 test_runner.py run account
    python3 test_runner.py run test_container
    python3 test_runner.py odoo
        """)
        return

    command = sys.argv[1].lower()

    if command == "generate":
        success = run_comprehensive_test_generation()
        print("✅ Test generation completed" if success else "❌ Test generation failed")

    elif command == "validate":
        success = validate_test_structure()
        print("✅ Test structure valid" if success else "❌ Test structure issues found")

    elif command == "coverage":
        success = show_test_coverage()
        print("✅ Coverage report generated" if success else "❌ Coverage report failed")

    elif command == "run":
        pattern = sys.argv[2] if len(sys.argv) > 2 else ""
        success = run_specific_tests(pattern)
        print("✅ Tests completed" if success else "❌ Some tests failed")

    elif command == "odoo":
        success = run_odoo_tests()
        print("✅ Odoo tests completed" if success else "❌ Odoo tests failed")

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python3 test_runner.py' for help")

if __name__ == "__main__":
    main()
