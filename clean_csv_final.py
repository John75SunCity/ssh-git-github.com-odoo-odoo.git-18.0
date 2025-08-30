#!/usr/bin/env python3
"""
Clean up the ir.model.access.csv file to remove invalid model entries and keep only valid models.
"""

import os
import re
import csv


def get_valid_models():
    """Get all valid model names from the module files."""
    models_dir = "records_management/models"
    valid_models = set()

    if not os.path.exists(models_dir):
        print(f"Models directory not found: {models_dir}")
        return valid_models

    for filename in os.listdir(models_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Find all _name = "model.name" patterns
                    matches = re.findall(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    for match in matches:
                        # Filter out invalid model names
                        if (
                            match
                            and not match.startswith("%")  # No format strings
                            and not match.startswith(" ")  # No leading spaces
                            and not match.endswith(" ")  # No trailing spaces
                            and not "," in match  # No commas
                            and not match.startswith(",")  # No leading commas
                            and len(match.strip()) > 0  # Not empty
                            and "." in match  # Must have dot (valid model format)
                            and not match.endswith(".user")  # No field-like names
                            and not match.endswith(".manager")
                            and not match.endswith("_id")
                            and not match
                            in ["name", "description", "display_name", "complete_name", "reference", "serial_number"]
                        ):
                            valid_models.add(match.strip())
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

    return valid_models


def clean_csv_file():
    """Clean the CSV file to keep only valid model entries."""
    csv_path = "records_management/security/ir.model.access.csv"
    valid_models = get_valid_models()

    print(f"Found {len(valid_models)} valid models:")
    for model in sorted(list(valid_models)[:10]):  # Show first 10
        print(f"  - {model}")
    if valid_models and len(valid_models) > 10:
        print(f"  ... and {len(valid_models) - 10} more")

    # Read existing CSV and filter valid entries
    valid_entries = []
    header = None

    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # Get header

                for row in reader:
                    if row and len(row) >= 4:
                        model_name = row[2].strip() if row and len(row) > 2 else ""
                        if model_name in valid_models:
                            valid_entries.append(row)

        except Exception as e:
            print(f"Error reading CSV: {e}")
            return

    print(f"\nFound {len(valid_entries)} valid entries in CSV")

    # Add missing models
    existing_models = {row[2].strip() for row in valid_entries if row and len(row) > 2}
    missing_models = valid_models - existing_models

    print(f"Adding {len(missing_models)} missing models...")

    for model in sorted(missing_models):
        # Add user access rule
        valid_entries.append(
            [
                f"access_{model.replace('.', '_')}_user",
                f"{model.replace('.', ' ')}",
                model,
                "records_management.group_records_user",
                "1",
                "1",
                "1",
                "0",
            ]
        )

        # Add manager access rule
        valid_entries.append(
            [
                f"access_{model.replace('.', '_')}_manager",
                f"{model.replace('.', ' ')}",
                model,
                "records_management.group_records_manager",
                "1",
                "1",
                "1",
                "1",
            ]
        )

    # Write clean CSV
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(valid_entries)

        print(f"\n✅ Cleaned CSV file: {len(valid_entries)} total entries")
        print(f"   - Header: 1 line")
        print(f"   - Valid entries: {len(valid_entries)} lines")

    except Exception as e:
        print(f"❌ Error writing CSV: {e}")


if __name__ == "__main__":
    print("🧹 Cleaning up ir.model.access.csv file...")
    clean_csv_file()
