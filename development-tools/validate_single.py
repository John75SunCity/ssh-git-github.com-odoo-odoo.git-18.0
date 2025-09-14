#!/usr/bin/env python3
"""
Single File Validator - Alias for comprehensive_validator.py
Usage: python3 validate_single.py path/to/file.xml
"""
import sys
import os

# Add the directory containing comprehensive_validator.py to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_validator import ComprehensiveValidator

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_single.py path/to/file.xml")
        return 1

    file_path = sys.argv[1]

    if not os.path.exists('records_management'):
        print("❌ Error: Run this script from the workspace root directory")
        return 1

    print("🔍 SINGLE FILE VALIDATOR")
    print("=" * 40)

    validator = ComprehensiveValidator('records_management')
    success = validator.validate_single_file(file_path)
    validator.print_results(file_path)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
