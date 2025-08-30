#!/usr/bin/env python3
"""
Simple script to clean up invalid entries in ir.model.access.csv
"""

import csv
import os


def clean_csv():
    csv_path = "records_management/security/ir.model.access.csv"

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return

    valid_lines = []
    invalid_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        valid_lines.append(header)

        for line_num, row in enumerate(reader, 2):
            if row and len(row) >= 4:
                model_name = row[2].strip() if row and len(row) > 2 else ""

                # Check if model name is valid
                if (
                    model_name
                    and not model_name.startswith("%")  # No format strings
                    and not model_name.startswith(" ")  # No leading spaces
                    and not model_name.endswith(" ")  # No trailing spaces
                    and not "," in model_name  # No commas
                    and not model_name.startswith(",")  # No leading commas
                    and len(model_name.strip()) > 0  # Not empty
                    and "." in model_name  # Must have dot (valid model format)
                    and not model_name.endswith(".user")  # No field-like names
                    and not model_name.endswith(".manager")
                    and not model_name.endswith("_id")
                    and not model_name
                    in ["name", "description", "display_name", "complete_name", "reference", "serial_number"]
                ):
                    valid_lines.append(row)
                else:
                    invalid_count += 1
                    print(f"Removing invalid entry at line {line_num}: {row}")

    print(f"\nRemoved {invalid_count} invalid entries")
    print(f"Keeping {len(valid_lines) - 1} valid entries")

    # Write back the cleaned CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(valid_lines)

    print(f"✅ Cleaned CSV saved to {csv_path}")


if __name__ == "__main__":
    clean_csv()
