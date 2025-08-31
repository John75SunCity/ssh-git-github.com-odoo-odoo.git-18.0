#!/usr/bin/env python3
"""
Clean the ir.model.access.csv file by removing endef main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    models_dir = os.path.join(script_dir, 'records_management', 'models')
    csv_path = os.path.join(script_dir, 'records_management', 'security', 'ir.model.access.csv')or models that don't exist.
"""

import os
import csv
import sys


def get_existing_models(models_dir):
    """Get list of existing model names from the models directory."""
    existing_models = set()

    # Skip these files as they're not models
    skip_files = {"__init__.py", "__pycache__"}

    for filename in os.listdir(models_dir):
        if filename in skip_files or not filename.endswith(".py"):
            continue

        # Convert filename to model name (remove .py extension)
        model_name = filename[:-3]  # Remove .py

        # Read the file to find the _name
        filepath = os.path.join(models_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Look for _name = 'model.name'
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("_name ="):
                        # Extract the model name
                        model_name_in_file = line.split("=")[1].strip().strip("'\"")
                        existing_models.add(model_name_in_file)
                        break
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    return existing_models


def clean_csv(csv_path, existing_models):
    """Clean the CSV file by removing entries for non-existent models."""
    cleaned_rows = []
    removed_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Read header
        cleaned_rows.append(header)

        for row in reader:
            if not row or len(row) < 3:
                continue

            model_id = row[2]  # model_id:id column

            if model_id in existing_models:
                cleaned_rows.append(row)
            else:
                removed_count += 1
                print(f"Removing entry for non-existent model: {model_id}")

    # Write cleaned CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)

    print(f"\nCleaned CSV file: removed {removed_count} entries for non-existent models")
    print(f"Remaining entries: {len(cleaned_rows) - 1}")  # Subtract header

    return removed_count


def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")

    models_dir = os.path.join(script_dir, "records_management", "models")
    csv_path = os.path.join(script_dir, "records_management", "security", "ir.model.access.csv")

    print(f"Models directory: {models_dir}")
    print(f"CSV path: {csv_path}")

    if not os.path.exists(models_dir):
        print(f"Models directory not found: {models_dir}")
        sys.exit(1)

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    print("Scanning existing models...")
    existing_models = get_existing_models(models_dir)
    print(f"Found {len(existing_models)} existing models")

    print("\nCleaning CSV file...")
    removed_count = clean_csv(csv_path, existing_models)

    print("\n✅ CSV cleaning completed successfully!")
    print(f"📊 Summary: Removed {removed_count} entries for non-existent models")


if __name__ == "__main__":
    main()
