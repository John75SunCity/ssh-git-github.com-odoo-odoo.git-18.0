#!/usr/bin/env python3
"""
Clean duplicate entries from ir.model.access.csv file
Removes duplicate access rules for the same model-group combinations
"""

import csv
import sys
from collections import defaultdict

def clean_duplicates(csv_file):
    """Clean duplicate entries from CSV file"""
    print(f"Reading {csv_file}...")

    # Read all entries
    entries = []
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header
        for row in reader:
            if len(row) >= 4:  # Ensure we have at least id, name, model_id, group_id
                entries.append(row)

    print(f"Found {len(entries)} total entries")

    # Group by model_id + group_id combination
    unique_entries = {}
    duplicates_found = 0

    for entry in entries:
        if len(entry) < 4:
            continue

        model_id = entry[2]  # model_id column
        group_id = entry[3]  # group_id column
        key = (model_id, group_id)

        if key in unique_entries:
            duplicates_found += 1
            print(f"DUPLICATE: {model_id} + {group_id}")
            print(f"  Keeping: {unique_entries[key][:2]}")
            print(f"  Removing: {entry[:2]}")
        else:
            unique_entries[key] = entry

    print(f"\nFound {duplicates_found} duplicate entries")
    print(f"Will keep {len(unique_entries)} unique entries")

    # Write cleaned file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)  # Write header
        for entry in unique_entries.values():
            writer.writerow(entry)

    print(f"Cleaned file written to {csv_file}")
    return len(unique_entries), duplicates_found

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clean_csv_duplicates.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    unique_count, duplicate_count = clean_duplicates(csv_file)
    print(f"\nSUMMARY: Removed {duplicate_count} duplicates, kept {unique_count} unique entries")
