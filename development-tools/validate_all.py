#!/usr/bin/env python3
"""
All Files Validator - Alias for comprehensive_validator.py
Usage: python3 validate_all.py
"""
import sys
import os

# Add the directory containing comprehensive_validator.py to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comprehensive_validator import ComprehensiveValidator

def main():
    if not os.path.exists('records_management'):
        print("❌ Error: Run this script from the workspace root directory")
        return 1

    print("🔍 ALL FILES VALIDATOR")
    print("=" * 40)

    validator = ComprehensiveValidator('records_management')
    validator.validate_all_files()
    validator.print_results()

    return 0

if __name__ == "__main__":
    sys.exit(main())
