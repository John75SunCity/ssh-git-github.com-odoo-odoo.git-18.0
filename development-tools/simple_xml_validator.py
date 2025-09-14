#!/usr/bin/env python3
"""
Simple XML Syntax Validator - focuses only on real parsing errors
"""

import os
import sys
import xml.etree.ElementTree as ET

def validate_xml_file(file_path):
    """Validate a single XML file for syntax errors"""
    try:
        tree = ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        error_line = getattr(e, 'lineno', 0)
        error_col = getattr(e, 'offset', 0)

        # Try to get context line
        context_line = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if error_line > 0 and error_line <= len(lines):
                    context_line = lines[error_line - 1].strip()
        except:
            pass

        return False, {
            'line': error_line,
            'column': error_col,
            'error': str(e),
            'context': context_line
        }
    except Exception as e:
        return False, {'error': f"Could not read file: {e}", 'line': 0}

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 simple_xml_validator.py <xml_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print(f"🔍 Validating XML syntax: {os.path.basename(file_path)}")

    is_valid, error = validate_xml_file(file_path)

    if is_valid:
        print("✅ XML syntax is valid")
    else:
        print(f"❌ XML syntax error:")
        print(f"   Line {error.get('line', 'unknown')}: {error.get('error', 'Unknown error')}")
        if error.get('context'):
            print(f"   Context: {error['context']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
