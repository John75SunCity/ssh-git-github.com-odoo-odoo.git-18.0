#!/usr/bin/env python3
"""
Remove Duplicate Fields Script

This script identifies and removes duplicate field definitions in Odoo model files.
It preserves the first occurrence of each field and removes subsequent duplicates.
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple


def extract_field_definitions(content: str) -> List[Tuple[str, int, str]]:
    """
    Extract field definitions from Python content.
    Returns list of (field_name, line_number, full_definition)
    """
    fields = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Match field definitions like: field_name = fields.FieldType(...)
        field_match = re.match(
            r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.", line.strip()
        )
        if field_match:
            field_name = field_match.group(1)
            full_definition = line

            # Handle multi-line field definitions
            if "(" in line and line.count("(") > line.count(")"):
                j = i
                while j < len(lines) and line.count("(") > line.count(")"):
                    j += 1
                    if j < len(lines):
                        full_definition += "\n" + lines[j - 1]
                        line += lines[j - 1]

            fields.append((field_name, i, full_definition))

    return fields


def find_duplicate_fields(
    fields: List[Tuple[str, int, str]],
) -> Dict[str, List[Tuple[int, str]]]:
    """
    Find duplicate field definitions.
    Returns dict of {field_name: [(line_number, definition), ...]}
    """
    field_occurrences = {}

    for field_name, line_num, definition in fields:
        if field_name not in field_occurrences:
            field_occurrences[field_name] = []
        field_occurrences[field_name].append((line_num, definition))

    # Return only fields that have duplicates
    return {
        name: occurrences
        for name, occurrences in field_occurrences.items()
        if len(occurrences) > 1
    }


def remove_duplicates_from_content(
    content: str, duplicates: Dict[str, List[Tuple[int, str]]]
) -> str:
    """
    Remove duplicate field definitions from content, keeping the first occurrence.
    """
    lines = content.split("\n")
    lines_to_remove = set()

    for field_name, occurrences in duplicates.items():
        # Keep the first occurrence, remove the rest
        for line_num, definition in occurrences[1:]:  # Skip first occurrence
            # Mark lines for removal
            def_lines = definition.split("\n")
            start_line = line_num - 1  # Convert to 0-based index

            for i in range(len(def_lines)):
                if start_line + i < len(lines):
                    lines_to_remove.add(start_line + i)

    # Remove marked lines
    filtered_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]

    return "\n".join(filtered_lines)


def process_model_file(filepath: str) -> Tuple[int, List[str]]:
    """
    Process a single model file to remove duplicate fields.
    Returns (number_of_duplicates_removed, list_of_duplicate_fields)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract field definitions
        fields = extract_field_definitions(content)

        # Find duplicates
        duplicates = find_duplicate_fields(fields)

        if duplicates:
            print(f"\n📁 {os.path.basename(filepath)}")
            duplicate_names = []
            total_removed = 0

            for field_name, occurrences in duplicates.items():
                duplicate_names.append(field_name)
                removed_count = len(occurrences) - 1  # Keep first occurrence
                total_removed += removed_count

                print(
                    f"  🔄 {field_name}: {len(occurrences)} occurrences → removing {removed_count}"
                )

            # Remove duplicates
            cleaned_content = remove_duplicates_from_content(content, duplicates)

            # Write back to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned_content)

            return total_removed, duplicate_names

        return 0, []

    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return 0, []


def main():
    """Main function to process all model files."""
    print("🧹 DUPLICATE FIELD REMOVAL TOOL")
    print("=" * 50)

    # Get records_management models directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(
        os.path.dirname(script_dir), "records_management", "models"
    )

    if not os.path.exists(models_dir):
        print(f"❌ Models directory not found: {models_dir}")
        sys.exit(1)

    print(f"📂 Processing models in: {models_dir}")

    total_files_processed = 0
    total_duplicates_removed = 0
    files_with_duplicates = []

    # Process all Python files in models directory
    for filename in sorted(os.listdir(models_dir)):
        if filename.endswith(".py") and filename != "__init__.py":
            filepath = os.path.join(models_dir, filename)

            removed_count, duplicate_fields = process_model_file(filepath)

            if removed_count > 0:
                total_duplicates_removed += removed_count
                files_with_duplicates.append(
                    (filename, removed_count, duplicate_fields)
                )

            total_files_processed += 1

    # Summary report
    print(f"\n📊 DUPLICATE REMOVAL SUMMARY")
    print("=" * 50)
    print(f"📁 Total files processed: {total_files_processed}")
    print(f"🔄 Files with duplicates: {len(files_with_duplicates)}")
    print(f"❌ Total duplicate fields removed: {total_duplicates_removed}")

    if files_with_duplicates:
        print(f"\n📋 FILES WITH DUPLICATES REMOVED:")
        for filename, count, fields in files_with_duplicates:
            print(f"  • {filename}: {count} duplicates removed")
            for field in fields[:3]:  # Show first 3 duplicate fields
                print(f"    - {field}")
            if len(fields) > 3:
                print(f"    ... and {len(fields) - 3} more")

    if total_duplicates_removed > 0:
        print(
            f"\n✅ Successfully removed {total_duplicates_removed} duplicate field definitions!"
        )
        print("🚀 Ready for clean field gap analysis.")
    else:
        print(f"\n✅ No duplicate fields found! All models are clean.")


if __name__ == "__main__":
    main()
